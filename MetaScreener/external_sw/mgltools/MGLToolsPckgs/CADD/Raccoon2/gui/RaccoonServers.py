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
            
from CADD.Raccoon2 import HelperFunctionsN3P as hf
import RaccoonSshTools as Rst
import RaccoonServices 
import RaccoonLibraries 
import sys
import json
from DebugTools import DebugObj
import threading 
import marshal
import zlib
import operator
import urllib
import os
import tarfile
from datetime import datetime
from time import sleep
import sys

# Laws are like sausages. It's better not to see them being made.
# Otto von Bismarck
# German Prussian politician (1815 - 1898)  

def dasbugger(msg):
    print msg
    sys.stdout.flush()
    sleep(3)


class RaccoonRemoteServer(DebugObj): 
    # XXX TODO:
    # add support for system and user paths
    # RACDIR_USER, RACDIR_SYSTEM
    # 
    # -add encryption for passwords
    #   http://www.blog.pythonlibrary.org/2010/10/20/downloading-encrypted-and-compressed-files-with-python/

    """
        RaccoonServer( address,             |
                       username,            |    Server connection data
                       password=None,       |    password is optional if keys are available 
                       usesyshostkeys=1     |--- in the user .ssh/ directory
                       autoaddmissingkeys(0)|    by default missing keys are added automatically
                       pkey=None            |    pkey='' specifies a public key file

                       name = ''            |--- Name of the RaccoonServer

                       racdir = None        |--- Set the initial path where to look for the 
                                                 config files. This value can be defined on
                                                 the server by setting the environmental
                                                 variable $RACDIR
                                                 (i.e. Bash: "export RACDIR='~/racdir/')

                       autoconnect (1)      |--- Open a connection when initialized

                       check       (1)      |___ check if the server is 'racconized'
                                            |    (i.e. necessary dirs are in place)
                                            
                       prepare     (0)      |---- racconize the server when initialized

                       autoscan    (1)      |---- autoscan=True 

                       debug       (0)      |---- activate debug mode (verbose)
                      )

    Supported systems are any *NIX system with a PBS or SGE scheduler.

    This is the structure of a racconized remote server:

    $RACDIR/ ***
        |
        +- bin/  store binaries installed by services
        |
        +- tmp/  ( store temporary stuff for calculations, like config files, etc)
        |
        +- services/  
        |     |          
        |     +- $(service1).conf ( service1 specific settings ) 
        |     |
        |     +- $(service2).conf ( service2 specific settings )
        |
        +- libraries/ ***
        |     |
        |     +- index.lib *** ( list of libraries+type(lig/rec/...) + data(properties,items,...))
        |     |
        |     +- $(libname1)/   [ OPTIONAL: if any in 'index.lib' ]
        |           |
        |           +- library.db    [ sqlite3|text|json ? ]
        |           |
        |           + 00
        |           |  |
        |           |  +-- mol001.pdbqt
        |           |  '-- mol002.pdbqt
        |           |
        |           + 01
        |           |
        |           ...
        |
        +- data/  ***
        |    |
        |    +- history.log  ***  ( history and status of jobs  SQLITE? JSON?)
        |    |
        |    +- $(outname1) -+  [ OPTIONAL: if 'outname1' listed in 'history.log' ]
        ...

    When racconizing a server, the following files will be created: 
     
        UPDATE!
     basic directories:
         $RACDIR, $RACDIR/config/, $RACDIR/libraries, $RACDIR/data

     basic files:
         $RACDIR/libraries/index.lib, $RACDIR/data/history.log

    """


    def __init__(self, address=None,                    # server address
                       username=None,                   # username MANDATORY
                       password=None,                   # password (optional if keys used and available)
                       name='RaccoonSsh_DockingServer', # name of the Raccoon Server
                       debug=False,                     # debug verbose mode
                       usesyshostkeys=True,             # try to connect without password using locally stored keys (POSIX OS ONLY)
                       autoaddmissingkeys=True,         # policy for adding the server to known hosts at first connection 
                       pkey=None,                       # filename of the encryption key to use
                       autoconnect=False,               # open connection with the server after initialization
                       check = True,                    # check if the server is racconized
                       prepare=False,                   # racconize the server if necessary
                       autoscan=True,                   # scan for services and resources upon connection
                       racdir=None,                     # use specified remote path as $RACDIR
                       scratchdir=None ):               # use local tempdir as scratch space (for services that need to write files)

        # debugging tools
        DebugObj.__init__(self, debug)

        # ssh client
        self.ssh = Rst.RaccoonSshClient(address, username, password, name, debug, 
                usesyshostkeys, autoaddmissingkeys, pkey, autoconnect)


        # file transfer (multi-threadable)
        self.transfer = None

        ### # on-going file transfers are stored here
        ### self._pending_transfers = []

        # DEFAULTS
        # base path for all the config, settings, data files 
        RACDIR = '~/raccoon'
        SCRATCH = os.path.expanduser('~') + os.sep + '.raccoon_tmp'
        
        # local scratch dir
        if not scratchdir == None:
            self.scratchdir = scratchdir
        else:
            self.scratchdir = SCRATCH

        # test if local scratch dir exists
        if not os.path.exists(self.scratchdir):
            if not hf.makeDir(fullpath=self.scratchdir):
                print "SERIOUS TROUBLES AHEAD: ERRORS CREATING TEMPDIR [%s]"  % self.scratchdir


        # Raccoon server specific properties

        # it is possible to connected to the server
        self.properties = { 'name': name, 'online' : False, 'hostname' : ''}
                          
        # server is raccoon-compliant (raccoonized)
        self.properties['ready'] = False

        # system info
        self.properties['system'] = { 'architecture' : None, # uname -m
                                      'scheduler'    : None, # pbs, sge 
                                      'os'           : None, # uname -o
                                      'kernel'       : None, # uname -r
                                      'hostname'     : None,
                                      'nodes'        : None,
                                      'scheduler_info': [],  # populated after scheduler identification
                                      'scheduler'    : '?',
                                    }

        #if not self.properties['scheduler'] == '?':
        # $RACDIR 
        if racdir:
            self.setRacPath(racdir)
        else:
            self.setRacPath(RACDIR)

        # this defines the raccoon-type, and it can be one of more of 'docking', 'md', 'docking_postprocess', ...
        self.properties['services'] =  {}

        # libraries available on the server (read from the Library Index file)
        # the content of the library index is defined by RaccoonLibraryManager.LibraryObj
        self.properties['libraries'] = [] 
        self.properties['libraries_problematic'] = []

        # list of unknown services found on the remote server (from config files)
        self._unknown_services = [] # = ( [ service_type, config_fname ] )
        # list of unknown library types found on the server (from index files)
        self._unknown_libs = [] # = ( lib_dict )

        # system info
        self.properties['system'] = { 'architecture' : None, # uname -m
                                      'scheduler'    : None, # pbs, sge 
                                      'os'           : None, # uname -o
                                      'kernel'       : None, # uname -r
                                      'hostname'     : None,
                                      'nodes'        : None,
                                      'scheduler_info': [],  # populated after scheduler identification
                                      'scheduler'    : '?',
                                    }

        #if not self.properties['scheduler'] == '?':
        # $RACDIR 
        if racdir:
            self.setRacPath(racdir)
        else:
            self.setRacPath(RACDIR)

        # this defines the raccoon-type, and it can be one of more of 'docking', 'md', 'docking_postprocess', ...
        self.properties['services'] =  {}

        # libraries available on the server (read from the Library Index file)
        # the content of the library index is defined by RaccoonLibraryManager.LibraryObj
        self.properties['libraries'] = [] 
        self.properties['libraries_problematic'] = []

        # list of unknown services found on the remote server (from config files)
        self._unknown_services = [] # = ( [ service_type, config_fname ] )
        # list of unknown library types found on the server (from index files)
        self._unknown_libs = [] # = ( lib_dict )


        # history of jobs submitted to the server
        self.history = {}

        if autoconnect:
            self.dprint("auto-connect requested. Opening connection")
            #conn = self.ssh.openconnection()
            conn = self.connect()
            if conn == 1:
                # check if the server is racconized already
                if check:
                    status = self.checkServerStatus()
                    self.dprint('auto-check requested. Status[%s]' % status)
                    if status:
                        # check if there are services configured on the server
                        if autoscan:
                            self.dprint('auto-scan requested. Scanning for services on the server...')
                            self.scan()
                # check if it needs to be prepared and it was requested so
                if prepare:
                    self.dprint('auto-prepare requested.')
                    self.racconize(force=False)
            else:
                self.dprint("connection not succesful [%s]" % conn)

    def hostname(self):
        """ return the host name as known by the host itself"""
        return self.properties['hostname']

    def name(self):
        """ return server name """
        return self.properties['name']

    def date(self):
        """ simple date function provided for services timestamps"""
        d = datetime.now()
        return [d.year, d.month, d.day, d.hour, d.minute, d.second ]

    def connect(self):
        """used to start connection from the external"""
        self.dprint("connection requested")
        conn = self.ssh.openconnection()
        if conn == 1:
            self.dprint("setting the mule transfer object") 
            self.transfer = Rst.FileMule( ssh = self.ssh, debug = self.debug)
            self.getHostname()
        else:
            self.dprint("disabling the mule transfer object") 
            self.transfer = None
            self.properties['hostname'] = ""
        return conn

    def is_connected(self):
        """ check if there is a working connection already open"""
        if not self.ssh.connection == None:
            return True
        return False

    def getHostname(self):
        """ query the server for its own name"""
        cmd = """hostname"""
        report = self.ssh.execmd(cmd)
        self.dprint("querying the server for hostname...")
        if report == False:
            self.dprint("error in connection")
            return False
        stdout, stderr = report
        if len(stdout):
            self.properties['hostname'] = stdout[0]
            return True
        return False

    def disconnect(self):
        """close open connections and disable transer object"""
        if not self.transfer == None and self.transfer._running:
            self.dprint("running transfer detected... stopping it")
            self.transfer.stop()
        self.transfer = None
        self.ssh.closeconnection()

    def scan(self):
        """ scan the server for libraries and services, and read history file"""
        if self.checkServerStatus():
            self.findLibraries()
            self.findServices()
            self.loadHistory()
        else:
            self.dprint("The server status is not true, returning")
            return

    def writeMarshal(self, fname, data, compression = False):
        """ write a serialized marshal data file 
            compression :  (bool) optional Zlib compression
        """
        self.dprint("Open file [%s] for writing" % (fname) )
        self.dprint("data type is [%s]" % type(data))

        report = self.ssh.openfile(fname, mode='wb')
        try:
            if not isinstance(report, tuple):
                self.dprint("ERROR: file pointer not generated: [%s]" % report)
                return False
            fp, sftp = report
        except:
            self.dprint("Error writing Marshal file [%s] : [%s]" % (fname, report))
            return False
        fp, sftp = report
        data = marshal.dumps(data)
        if compression:
            data = zlib.compress(data)
        fp.write(data)
        fp.close()
        sftp.close()
        return True

        
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
        report = self.ssh.openfile(fname, mode='w')
        self.dprint("data type is [%s]" % type(data))
        try:
            if not isinstance(report, tuple):
                self.dprint("ERROR: file pointer not generated: [%s]" % report)
                #exit(1)
                return False
            fp, sftp = report
        except:
            self.dprint("Error writing JSON file [%s] : [%s]" % (fname, report))
            #fp.close()
            #sftp.close()
            return False
        if compression:
            self.dprint("writing (COMPRESSED) to [%s]" % fp)
            data = json.dumps(data, indent=2)
            zdata = zlib.compress(data)
            fp.write(zdata)
        else:
            self.dprint("writing (UNCOMPRESSED) to [%s]" % fp)
            json.dump(data, fp, indent=2)
        self.dprint("Data written")
        fp.close()
        sftp.close()
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
        report = self.ssh.openfile(fname, mode='r')
        try:
            fp, sftp = report
        except:
            self.dprint("Error reading JSON file [%s] : [%]" % (fname, report))
            return False
        
        data = fp.read()
        fp.close()
        sftp.close()
        if compression:
            data = zlib.decompress(data)
        try:
            data = json.loads(data, object_hook=hf.jsonhelper)
        except:
            self.dprint("Problem [%s]" % sys.exc_info()[1])
            return False
        self.dprint("data type read is [%s]" % type(data))
        return data

    def readMarshal(self, fname, compression=False):
        """ read a serialized marshal data file
            
            compression :  (bool) optional Zlib compression
        """
        self.dprint("Open file for reading [%s]" % (fname))
        report = self.ssh.openfile(fname, mode='r')
        try:
            fp, sftp = report
        except:
            self.dprint("Error reading Marshal file [%s] : [%]" % (fname, report))
        try:
            data = fp.read()
            fp.close()
            sftp.close()
            if compression:
                data = zlib.decompress(data)
            data = marshal.loads(data)
            return data
        except:
            self.dprint("Problem [%s]" % sys.exc_info()[1])
            return False

    def writetext(self, fname, text):
        """ write a text file in specified location"""
        self.dprint("writing text file [%s]" % fname)
        try:
            fp, sftp = self.ssh.openfile(fname, mode='w')
            fp.write(text)
            fp.close()
            sftp.close()
            return True
        except:
            error = sys.exc_info()[1]
            self.dprint(error)
            return error


    def setRacPath(self, path):
        """ set the RacDir path variable and configure
            all depending variables basing
        """
        CONFIG_PATH = 'services'
        LIBRARY_PATH = 'libraries'
        LIBRARY_FILE = 'index.lib'
        DATA_PATH = 'data'
        BIN_PATH = 'bin'
        TMP_PATH = 'tmp'
        HISTORY_FILE = 'history.log'

        self.properties['racdir'] = path + '/'
        # config directory name ( $RACDIR/'services' )
        self.properties['config_path'] = self.properties['racdir'] + CONFIG_PATH + '/'
        # bin path
        self.properties['bin_path'] = self.properties['racdir'] + BIN_PATH + '/'
        # temp path
        self.properties['temp_path'] = self.properties['racdir'] + TMP_PATH + '/'
        # data path
        self.properties['data_path'] = self.properties['racdir'] + DATA_PATH + '/'
        # libraries path
        self.properties['library_path'] = self.properties['racdir'] + LIBRARY_PATH + '/'
        # libraries index file
        self.properties['library_index'] = self.properties['library_path'] + LIBRARY_FILE
        # history file
        self.properties['history'] = self.properties['data_path'] + HISTORY_FILE


    def getRacPath(self):
        """ return the current RACDIR path 
            test if there is environment variable RACDIR 
            set, or else use the default value
        """
        # XXX THIS FUNCTION MUST BE UPDATED TO 
        # XXX HANDLE SYSTEM AND USER DIRS TOGETHER
        cmd = 'printenv | grep RACDIR'
        report = self.ssh.execmd(cmd)
        if report == False:
            #print "getRacPath> No connection"
            return
        stdout, stderr = report
        if len(stdout):
            found = stdout[0]
            if not found == '':
                racdir = found.split("=")[1]
                self.dprint("Found remote env variable $RACDIR on the server [%s]"% racdir)
                self.properties['racdir']
        return self.properties['racdir']

    def getConfigPath(self):
        """ return the path containing the services config files"""
        return self.properties['config_path']

    def getLibraryPath(self):
        """ return the library path """
        return self.properties['library_path']

    def getLibraryIndexFilename(self):
        """return the library index file"""
        return self.properties['library_index']

    def getTempPath(self):
        """return the path to the temp directory"""
        return self.properties['temp_path']

    def getBinPath(self):
        """return the path to the bin directory"""
        return self.properties['bin_path']

    # data directory
    def getDataPath(self):
        """ return the path where data is stored """
        return self.properties['data_path']

    # history stuff
    def getHistoryFilename(self):
        """ return the history of jobs run on the server"""
        return self.properties['history']
        
    def loadHistory(self):
        """ return the history of jobs submitted to the server
        """
        fname = self.getHistoryFilename()
        self.dprint("reading [%s] history file" % fname)
        self.history = self.readJson(fname)
        if self.history == False:
            self.dprint("empty/unreadable history file")
            self.history = {}

    def saveHistory(self):
        """ return the history of jobs run on the server
        """
        fname = self.getHistoryFilename()
        self.dprint("writing [%s] history file" % fname)
        return self.writeJson(fname, self.history)

        
    def loadLibraryIndex(self):
        """ read and parse the master Library Index file
            (JSON) containing libraries installed on the server
            and return the library index (DICT)

            the content of the library index is defined by 
            RaccoonLibraryManager.LibraryObj
        """
        fname = self.getLibraryIndexFilename()
        self.dprint("reading library index file [%s]" % fname, new=1)
        libindex = self.readJson(fname)
        
        del self.properties['libraries'][:]
        del self._unknown_libs[:]
        if libindex == False:
            self.dprint("error library index")
            return False
        print "     >> FINISHED READING LIB INDEX"
        sys.stdout.flush()
        sleep(2)

        unknonw_lib = []
        for data in libindex:
            lib = RaccoonLibraries.knownlibraries.get(data['type'], None)

            if lib:
                #print "LIBINDEX FOUND>>>> ", data['index_file']
                lib = lib(server = self, info = data) 
                dasbugger("LIBRARY READ:  "+data['name'])
                if lib.ready:
                    self.properties['libraries'].append(lib)
                else:
                    self.properties['libraries_problematic'].append(data)
            else:
                self._unknown_libs.append(data)
        self.properties['libraries'] = sorted(self.properties['libraries'],
                                        key = operator.methodcaller('name') )

        self.dprint(self.properties['libraries'])

    def saveLibraryIndex(self):
        """ write the list of libraries installed on the server 
            in the master Library Index file

            the content of the library index is defined by 
            RaccoonLibraryManager.LibraryObj
        """
        fname = self.getLibraryIndexFilename()
        self.dprint("writing library index file [%s]" % fname, new=1)
        data = [ x.info for x in self.properties['libraries'] ]
        report = self.writeJson(fname, data)
        if report == False:
            self.dprint("library index writing failed")
        self.dprint("library index writing successful")
        return report

    def delLibrary(self, name, delfiles=True):
        """ unregister a library and update the library index """
        lib = self.getLibrary(name)
        if lib:
            if delfiles:
                self.dprint('deleting files...')
                path = lib.getFilesPath()
                self.ssh.delfiles([path])
            self.properties['libraries'].remove(lib)
            self.saveLibraryIndex()
            return True
        else:
            self.dprint('no library with name [%s]' % name)
            return False

    def getLibraries(self):
        """ return libraries list"""
        return self.properties['libraries']

    def getLibrary(self, name):
        """ return a library with name"""
        for l in self.getLibraries():
            if l.name() == name:
                return l
        return None
            
    def getLibraryNames(self):
        """ return list of library names"""
        return [ l.name() for l in self.getLibraries() ]

    
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
            self.dprint("\nEXP POOL [%s]" % ",".join(exp_pool) )
            for e in exp_pool:
                if not e in self.history[p].keys():
                    self.dprint("*NOT FOUND* (no experiments with this name)") 
                    return ()
                else:
                    if name in self.history[p][e].keys():
                        found = ( p, e, name ) 
                        self.dprint("\n*FOUND* [%s|%s|%s]" % found)
                        return found
        self.dprint("*NOT FOUND*") 
        return ()



    def getJobData(self, jobdata): # prj=None, exp=None, name=None):
        """ return info about a job prj|exp|name"""
        prj, exp, name = jobdata
        self.dprint("requested [%s|%s|%s]" % (prj, exp, name) )
        if prj == exp == name == None:
            return ()
        try:
            self.dprint("found job")
            return self.history[prj][exp][name]
        except:
            self.dprint("no jobs")
            return ()

    def makeExperimentDir(self, job_info={}, _type='vs'):
        """ create the remote directory where the calculation 
            is going to be performed

            _type : set the type of calculation to be performed
                    so it adds an extra dir for the specific type (i.e. "vs")

            NOTE: _type option is going to be ignored to simplify directory management
                when deleting jobs.
                FIXME? possibly it could be managed in a different way if other kind of
                       services will be implemented

        """
        base = self.getDataPath()
        self.dprint("base data path [%s], experiment type[%s]" % (base, _type))
        prj = job_info['prj']
        exp = job_info['exp']
        tag = job_info['tag']
        # makedir
        #maindir = '/'.join([base, prj, exp, _type]) # $RACDIR/data/project/exp/_type # XXX removed to simplify
        maindir = '/'.join([base, prj, exp]) # $RACDIR/data/project/exp/_type
        maindir = "".join(hf.validPath(maindir))
        self.dprint("creating dir [%s]" % maindir)
        status = self.ssh.makedir(maindir)
        if status ==True:
            return True, maindir
        else:
            return False, status


    def manifesto(self, _format='json'):
        """ collects the information about 
            the server available so far.

        _format can be 'json' or 'none' ( = python dict)

        """
        p = self.properties
        t = self.serviceTypes()
        #s = self.services()
        manifesto = {}
        # sys info = p['system']
        manifesto = {'name': p['name'],
                     'services' : {},
                     'host_info': p['system'],
                     'libraries' : {},
                    }
        skip_kw = set([ 'service', 'command', 'file', 'validated', 'file',
                        'upload', 'outdir',
                        ])
        self.dprint("collecting data from the known services", args=True)
        for _type in t:
            manifesto['services'][_type] = []
            for service in self.services(_type):
                info = {}
                s = service.config
                for kw in set(s.keys())-skip_kw:
                    info[kw] = s[kw]
                manifesto['services'][_type].append(info)


        libs = self.properties['libraries']
        lib_kw = [ 'comments', 'count', 'date', 'format', 'type' ]
        if len(libs) > 0:
            self.dprint("[%d] libraries found" % len(libs))
            for l in libs:
                name = l.info['name']
                info = {}
                for kw in lib_kw:
                    info[kw] = l.info[kw]
                manifesto['libraries'][name] = info
        else:
            self.dprint("no libraries found")

        if _format == 'json':
            manifesto = json.dumps(manifesto, indent=3, sort_keys=True)
            self.dprint("JSON manifesto requested:\n\n %s\n" % manifesto)
        return manifesto


    def systemInfo(self, key=None):
        """ return specific system info (i.e. key = 'scheduler'),
            or the entire info dictionary collected so far
        """
        if key:
            return self.properties['system'].get(key, 'unknown')
        return self.properties['system']


    def isServerAccessible(self):
        """ check if it is possible to open a connection to the 
            server and update the self.properties['online' status
        """
        self.dprint("attempting opening a connection")
        status = self.ssh.openconnection()
        if not status == 1:
            self.dprint("error opening the connection", status)
            print "isServerAccessible> ERROR: %s"% status
        else:
            self.dprint("server replied and is online!")
            self.properties['online'] = True

    def getSystemInfo(self):
        """gather information on the server
           and set values in self.properties['system']
        """
        # get the hostname
        self._getHostname()
        # find which architecture is available
        self._archInfo()
        # find which scheduler(s?) are available, if any
        self._schedulerInfo()

    def _getHostname(self):
        """ find and store server hostname """
        self.properties['system']['hostname'] = ""
        cmd = """hostname"""
        report = self.ssh.execmd(cmd)
        if report == False:
            print "_getHostname> connection error"
            return
        stdout, stderr = report
        self.properties['system']['hostname'] = stdout[0]
        
    def _archInfo(self):
        """ gather general information about the system 
            hardware/software
        """
        # arch -> x86_64(garibaldi,atara), ppc(esau)
        uname_opt = [ ['architecture', '-m'],
                      ['os', '-o'],
                      ['kernel', '-r']
                    ]
        for kw, opt in uname_opt:
            self.properties['system'][kw] = None
            cmd = 'uname %s' % opt
            report = self.ssh.execmd(cmd)
            if report == False:
                return False
            stdout = report[0]
            stderr = report[1]
            if not len(stderr)>0 and len(stdout):
                self.properties['system'][kw] = stdout[0].strip()
            else:
                print "_archInfo> ERROR REPORT [%s][%s]" % (kw, opt), report
                

    def _schedulerInfo(self):
        """ try to guess which scheduler is installed on the
            remote cluster

            supported schedulers are pbs and sge
        """
        self.properties['system']['scheduler'] = '?'
        # PBS
        if not self._testPbs():
            self._testSge()
        

    def _testPbs(self):
        """ try to identify the SGE scheduler on the cluster
        
               # PBS attributes (max job arrays) : http://linux.die.net/man/7/pbs_server_attributes
        # http://www.usc.edu/hpcc/pbsman/man7/pbs_server_attributes.html 
        
        """
        found = False
        self.dprint("Testing for PBS..."),
        # XXX Better using env? 
        # cmd = """printenv | grep PBS ..."""
        cmd = """man 1 qsub >x ; grep -iq pbs x ; echo $?; rm x"""
        report = self.ssh.execmd(cmd)
        if report == False:
            return False
        stdout = report[0]
        if len(stdout):
            stdout = stdout[0]
        self.dprint("STDOUT[%s]" % stdout)
        if str(stdout) == '0':
            found = True
        else:
            return False
        self.properties['system']['scheduler'] = 'pbs'
        self.properties['system']['nodes'] = '?'
        self.dprint("Found possible PBS scheduler")

        self.dprint("checking nodes..."),
        cmd = """pbsnodes -l all | wc -l"""
        report = self.ssh.execmd(cmd)
        if report == False:
            return False
        try:
            stdout = report[0][0]
            self.dprint("found [%s]" % stdout)
            self.properties['system']['nodes'] = int(stdout)
        except:
            self.dprint("Error [%s]" % sys.exc_info()[1])
            return False
        # get general scheduler info
        cmd = '''qmgr -c "list server"'''
        report = self.ssh.execmd(cmd)
        if report == False:
            self.dprint("WARNING: problem communicating with the PBS server (possible troubles ahead)")
            return True
        stdout, stderr = report

        self.properties['system']['scheduler_info'] = {}
        settings = [ ['max_job_array_size', int],
                     ['default_queue', str],
                     ['resources_assigned.ncpus', int],
                     ['resources_assigned.nodect', int],
                     ['default_queue', str],
                   ]
        for line in stdout:
            for kw, fn in settings:
                if kw in line:
                    v = line.split('=')[1].strip()
                    self.properties['system']['scheduler_info'][kw] = fn(v)
        return True


    def _testSge(self):
        """ try to identify the SGE scheduler on the cluster"""

        # SGE
        self.dprint("Testing for SGE..."),
        # XXX Better using env? 
        # cmd = """printenv | grep SGE ..."""
        cmd = """man 1 qsub  > x;  grep -qi "Grid Engine"  x ; echo $?; rm x"""
        report = self.ssh.execmd(cmd)
        if report == False:
            return False
        stdout = report[0]
        self.dprint("STDOUT[%s]" % stdout)
        if len(stdout):
            stdout = stdout[0]
        if str(stdout) == '0':
            self.properties['system']['scheduler'] = 'sge'
            self.properties['system']['nodes'] = '?'
            self.dprint("Found possible SGE scheduler")
        else:
            self.dprint("No known schedulers found on the server.")
            return False
        self.dprint("checking nodes..."),
        cmd = """qhost | wc -l"""
        report = self.ssh.execmd(cmd)
        if report == False:
            return False
        self.properties['system']['scheduler_info'] = {}
        try:
            stdout = int(report[0][0])
            self.dprint("found [%s]... minus 3 lines = %s " % (stdout, stdout-3 ))
            self.properties['system']['nodes'] = stdout-3
            #self.properties['system']['scheduler_info'] = ['not available yet, TODO']
        except:
            self.dprint("Error [%s]" % sys.exc_info()[1])
            self.properties['system']['nodes'] = "(error)"
        # max jobs per array 
        cmd = """qconf -sconf | grep max_aj_instances | awk '{print $2}'"""
        report = self.ssh.execmd(cmd)
        if report == False:
            return False
        try:
            stdout = int(report[0][0])
            self.dprint("found [%s]... max_aj_instances" % (stdout))
            self.properties['system']['scheduler_info']['max_aj_instances'] = stdout
        except:
            self.dprint("'max_aj_instances' not found")
        return True

    def getScheduler(self):
        """ return the scheduler found on the cluster"""
        return self.properties['system']['scheduler']

    def getMaxJobsPerArray(self):
        """ return the maximum number of jobs that
            a job array can spawn
        """
        sched = self.getScheduler()
        if sched == 'pbs':
            kw = 'max_job_array_size'
        elif sched == 'sge':
            kw = 'max_aj_instances'
        value = self.properties['system']['scheduler_info'].get(kw, None)
        return value

    def checkRaccoonDir(self):
        """ check if the raccoon dir exists on the server """
        if not self.ssh.exists(self.getRacPath()):
            self.dprint("missing Raccoon dir [%s|%s]" % (self.getRacPath(), 
                self.ssh.normpath(self.getRacPath() )))
            return False
        return True

    def checkConfigPath(self):
        """ check if the config path exists on the server """
        if not self.ssh.exists(self.getConfigPath()):
            self.dprint("missing Config dir [%s|%s]" % (self.getConfigPath(),
                self.ssh.normpath(self.getConfigPath() )))
            return False
        return True

    def checkLibraryPath(self):
        """ check if the library path exists on the server """
        if not self.ssh.exists(self.getLibraryPath()):
            self.dprint("missing Library dir [%s|%s]" % (self.getLibraryPath(), 
            self.ssh.normpath(self.getLibraryPath() )))
            return False
        return True

    def checkDataPath(self):
        """ check if data path exists on the server """
        if not self.ssh.exists(self.getDataPath()):
            self.dprint("missing Data dir [%s|%s]" % (self.getDataPath(), 
            self.ssh.normpath(self.getDataPath() )))
            return False
        return True

    def checkTempPath(self):
        """ check if temp path exists on the server """
        if not self.ssh.exists(self.getTempPath()):
            self.dprint("missing Temp dir [%s|%s]" % (self.getTempPath(), 
            self.ssh.normpath(self.getTempPath() )))
            return False
        return True


    def checkBinPath(self):
        """ check if bin path exists on the server """
        if not self.ssh.exists(self.getBinPath()):
            self.dprint("missing Bin dir [%s|%s]" % (self.getBinPath(), 
            self.ssh.normpath(self.getBinPath() )))
            return False
        return True


    def checkLibraryIndex(self):
        """ check if library index file exists on the server """
        if not self.ssh.exists(self.getLibraryIndexFilename()):
            self.dprint("missing library index file [%s|%s]" % (self.getLibraryIndexFilename(),
                self.ssh.normpath(self.getLibraryIndexFilename() )))
            return False
        return True

    def checkHistoryFile(self):
        """ check if history file exists on the server """
        if not self.ssh.exists(self.getHistoryFilename()):
            self.dprint("missing services config file [%s|%s]" % (self.getHistoryFilename(),
                self.ssh.normpath(self.getHistoryFilename() )))
            return False
        return True

    def cleanTemp(self):
        """ clean up all files left in the temp dir
            it should be used before closing a session
        """
        self.dprint("deleting dir [%s]" %  self.getTempPath() )
        self.ssh.delfiles([self.getTempPath()])
        self.dprint("re-creating dir [%s]" %  self.getTempPath() )
        self.ssh.makedir(self.getTempPath())


    def checkServerStatus(self):
        """
        update the self.properties dictionary

        connect to the server and check if the raccoon dir is present
        if present, read the config file:
          locate the lig library path (set the variable if present)
        """
        # check if the server is reachable
        self.isServerAccessible()
        if not self.properties['online']:
            self.dprint("server is not online")
            return False
        # gather system info
        #print "GETSYSINFO"
        #sys.stdout.flush()
        self.getSystemInfo()


        # the status of the server is set to not ready...
        self.properties['ready'] = False
        
        data_to_check = [ [self.checkRaccoonDir, 'Raccoon dir'],
                          [self.checkConfigPath, 'Config dir'],
                          [self.checkLibraryPath, 'Library dir'],
                          [self.checkDataPath, 'Data dir'],
                          [self.checkTempPath, 'Temp dir'],
                          [self.checkBinPath, 'Bin dir'],
                          [self.checkLibraryIndex, 'Library index'],
                          [self.checkHistoryFile, 'History file'],
                        ]

        for checker, msg in data_to_check:
            if not checker():
                self.dprint('%s ***NOT PASSED***' % msg)
                return False
            else:
                self.dprint('%s [ PASSED ]' % msg)
        self.dprint("checking scheduler")
        if not self.properties['system']['scheduler'] == '?':
            # ALL TEST PASSED, update status
            self.properties['ready'] = True
            return True
        else:
            self.dprint("unknown/missing scheduler")
            return False
        self.properties['ready'] = True
        return True
        

    def racconize(self, force=False):
        """ racconize a server if necessary"""

        if self.properties['ready']:
            if not force:
                self.dprint("self.properties report the server as 'ready'")
                return True
        # checking directories
        if not self._checksetupdirs(force=force):
            print "ERROR: Racconization not successful! [step: checking directories]"
            return False
        # check files
        if not self._checksetupfiles(force=force):
            print "ERROR: Racconization not successful! [step: checking files]"
            return False
        #print "[ DONE ]"
        self.properties['ready'] = True
        return True



    def _checksetupdirs(self, force=False):
        """ initialize directories that are necessary for the 
            raccoonification process
            
            when force=1 is used, any pre-existing file will be 
            overwritten
        """
                         # checker,              name_getter      comment
        dirs_to_check = [ [self.checkRaccoonDir, self.getRacPath, 'Raccoon directory'],
                          [self.checkConfigPath, self.getConfigPath, 'Config directory'],
                          [self.checkLibraryPath, self.getLibraryPath, 'Library directory'],
                          [self.checkDataPath, self.getDataPath, 'Data directory'],
                          [self.checkTempPath, self.getTempPath, 'Temp directory'],
                          [self.checkBinPath, self.getBinPath, 'Bin directory'],
                        ]
        for checker, dirname, msg in dirs_to_check:
            makedir = True
            path = dirname()
            if checker():
                if force:
                    self.dprint("Directory [%s] already exists [FORCING DELETION...]" %  path )
                    # XXX here a backup could occur...?
                    self.ssh.delfiles([path] )
                    self.dprint("Directory [%s] already exists [ >>DELETED<< ]" %  path )
                else:
                    self.dprint("Directory [%s] already exists [SKIPPING] (use force to overwrite it)" %  path )
                    makedir = False
            if makedir:
                try:
                    self.dprint("Creating directory [%s]" % path)
                    self.ssh.makedir( path )
                except:
                    self.dprint("_checksetupdirs> Error creating %s [%s]: %s" % (msg, path, sys.exc_info()[1]) )
                    return False
        return True


    def _checksetupfiles(self, force=False):
        """ initialize config files that are necessary for the
            raccoonification process
            
            when force=1 is used, any pre-existing file will be 
            overwritten
        """           
                         # checker, name_getter, maker, comment
        files_to_check = [ 
                          ### [ self.checkServicesConfig, self.getServicesConfFilename, 
                          ###  self.makeServicesConf, 'Services configuration file'],
                          ### DISABLED NOW IT IS MANAGED BY THE SERVICE ITSELF

                           [ self.checkLibraryIndex, self.getLibraryIndexFilename, 
                             self.makeLibraryIndex, 'Library index file'],

                           [ self.checkHistoryFile, self.getHistoryFilename, 
                             self.makeHistoryFile, 'History log file'],
                         ]
        for checker, fnamegetter, maker, msg in files_to_check:
            makefile = True
            filename = fnamegetter()
            self.dprint("Checking file [%s]" % filename),
            if checker():
                self.dprint("FOUND"),
                if force:
                    self.dprint("File [%s] already exists [FORCING DELETION]" %  filename )
                    self.ssh.delfiles( [filename] )
                else:
                    self.dprint("File [%s] already exists [SKIPPING] (use force to overwrite it)" %  filename )
                    makefile = True
            if makefile:
                try:
                    self.dprint("Creating file [%s]..." % filename),
                    maker( {'fname': filename })
                    #print "[SUCCESS]"
                except:
                    #print "_checksetupfiles> Error creating %s [%s]: %s" % (msg, filename, sys.exc_info()[1])
                    self.dprint("_checksetupfiles> Error creating %s [%s]: %s" % (msg, filename, sys.exc_info()[1]) )
                    return False
        return True


    def makeLibraryIndex(self, library_info={}):
        """ initialize the library index file
            generating an empty file
        """
        fname = library_info['fname']
        self.writetext(fname, '{}')
        #self.ssh.touchfile(fname)

    def makeHistoryFile(self, history_info = {}):
        """ initialize the history log file
            generating an empty file
        """
        fname = history_info['fname']
        self.ssh.touchfile(fname)

    def findLibraries(self):
        """
            scan the master library file for registered 
            libraries on the server
        """
        self.dprint("searching for libraries on the server")
        self.loadLibraryIndex()

    def findServices(self):
        """ scan the directory containing services $RACDIR/$CONFIG
            and return the services found
        """
        if not self.properties['online']:
            #print "Not connected to the server yet. Connect to it with .openconnection()"
            return
            
        if not self.properties['ready']:
            #print "Server not racconized yet. Prepare it first with .racconize()"
            return

        # delete previous services
        del self.properties['services']
        self.properties['services'] = {}
        del self._unknown_services[:]

        path = self.getConfigPath() 
        config = self.ssh.listdir(path)
        if not config:
            self.dprint("No config files found in %s" % path)
            return False
        self.dprint("FOUND %d FILES %s" % (len(config), config))
        services = []
        problematic = []
        for c in config:
            if c[-5:] == ".conf":
                fname = path + '/' + c
                self.dprint("parsing file [%s]" % fname)
                srv, issues = self.parseServiceConfig(fname)
                if len(issues):
                    self.dprint('problematic lines in file: [%s]' % str(issues))
                if 'service' in srv.keys():
                    if len(srv) > 1: # the kw 'file' is always present
                        services.append(srv)
                        self.dprint('config data accepted')
                    else:
                        problematic.append([fname, 'not enough keywords'])
                        self.dprint('not enough keywords')
                else:
                    problematic.append([fname, 'missing "service" kw'])
                    self.dprint('missing server kw in config file')
        for service_dict in services:
            # register services
            stype = service_dict['service']
            if stype in RaccoonServices.knownservices.keys():
                self.addService(service_dict)
            else:
                self.dprint("WARNING: unrecognized service type: %s" % stype)
                self.dprint("config file: %s" % service_dict['file'] )
                self.dprint("unknown service[%s] file[%s]" % (stype, service_dict['file']))
                problematic.append([fname, 'unknown service type'])
                self._unknown_services.append( [ stype, service_dict['file'] ] )
        return problematic
                
    def addServiceFromConf(self, fname):
        """ add a service by parsing a config file
        """
        self.dprint("adding service from [%s]" % fname)
        conf, problems = self.parseServiceConfig(self.getConfigPath() + fname)
        self.dprint("SERVCONFIG")
        self.dprint(conf)
        self.dprint(problems)
        return self.addService(service_dict = conf)

    def addService(self, service_dict = {}, allowduplicates=False, debug=False):
        """ add a service to the list of known services 
        
            services are grouped by type
        """
        stype = service_dict['service']

        self.dprint("adding service [%s], type[%s], from config[%s]" % (service_dict['name'],
            stype, service_dict['file']), new=True )
        if not stype in self.properties['services'].keys():
            # first time this server type is found
            self.properties['services'][stype] = []
        status = { 'accepted' : False, 'duplicate' : [] }
        # find possible duplicated services
        all_services_config = [ x.config  for x in self.services(_type= stype) ]
        skip_kw = set([ 'name', 'comment', 'validated', 'file'])

        for conf in all_services_config:
            conf_kw = set(conf.keys())
            new_conf_kw = set(service_dict.keys())
            kw_to_check = (conf_kw - skip_kw) & ( new_conf_kw - skip_kw)
            self.dprint("%d common settings: %s" % (len(kw_to_check), kw_to_check) )
            c = 0
            for kw in kw_to_check:
                if service_dict[kw] == conf[kw]:
                    c+=1
            if len(kw_to_check) == c:
                status['duplicate'].append(conf['file'])
                self.dprint("[file:%s] found a service with identical config: [%s]" % (service_dict['file'], 
                    status['duplicate'][-1]) )
                if allowduplicates: # accept 
                    self.dprint("duplicate found but allowed. Continuing...")
                else: # reject
                    status['accepted'] = False
                    self.dprint("duplicates not allowed (use allowduplicates=1 to override)")
                    return status
        self.dprint("Registering service...")    
        status['accepted'] = True
        srv = RaccoonServices.knownservices[stype](server=self, config = service_dict, debug=self.debug )
        self.properties['services'][stype].append(srv)
        self.dprint("%d duplicates found: %s" % (len(status['duplicate']), status['duplicate']))
        # FIXME the new service event should be triggered here
        return status

    def delService(self, service_name, removeconf=True):
        """remove a registered service"""
        self.dprint("asked service_name[%s]" % service_name)
        srv = self.services(name=service_name)
        if len(srv):
            srv = srv[0]
            # remove config file
            if removeconf:
                conf = srv.config['file']
                self.dprint("removing config file [%s]" % conf)
                self.ssh.delfiles([conf])
            # unregister the service from the server
            _type = srv._srvtype
            idx = self.properties['services'][_type].index(srv)
            self.properties['services'][_type].pop(idx)
            self.dprint("service [%s] removed" % srv )
        # EVENT? 


    # XXX NOT USED?
    def writeconfig(self, fname, config):
        """ write service config data in required file
            in the services config location
        """
        # XXX NOT SURE IF THIS SHUOLD BE MANAGED BY 
        #    THE SERVICE ITSELF OR THE SERVER
        fullpath = self.getRacDir() + '/' + fname
        self.dprint('write config file [%s]' % fullpath)
        return self.writetext(fullpath, config)
    # XXX NOT USED

        
    def services(self, _type=None, name=None):
        """"Return all list(services) that have been found and registered

            if _type is requested, return all services matching the request

            if no _type is found or no services are registered, [] is returned.
        """
        if not _type == None and not name == None:
            return False
        if _type:
            return self.properties['services'].get(_type, [])
        srv = []
        for t in self.properties['services']:
            for s in self.properties['services'][t]:
                if (not name == None):
                    if s.config['name'] == name:
                        srv.append(s)
                else:
                    srv.append(s)
        self.dprint("Services %d retrieved" % len(srv))
        return srv

    def service(self, name):
        """ retrieve service by name """
        for t in self.serviceTypes():
            for s in self.properties['services'][t]:
                if s.config['name'] == name:
                    return s
        return None


    def serviceTypes(self):
        """ return found service types """
        return sorted(self.properties['services'].keys())

    def removeService(self, name=None, _type = None):
        """ remove a service for the list of registered services """
        if name == None and _type == None:
            self.dprint("name and _type are None, returning")
            return
        if not name == None and not _type == None:
            self.dprint("both name[%s] and type[%s] requested: conflict!" % (name, _type) )
        # remove by type
        if not _type == None:
            if not _type in self.properties['services'].keys():
                self.dprint( "No services of type [%s]" % _type)
                return
            del self.properties['services'][_type]
            return
        # remove by name
        for t in self.properties['services']:
            for s in self.properties[t]:
                srv = self.properties['services'][t][s]
                if srv.name == name:
                    self.properties['services'][t].pop(srv)
                    return

    def parseServiceConfig(self, fname):
        """ parse service config file and return a 
            dictionary description of the service

            config file has the format:

            kw = value

            it can contains comments: any text after the '#' 
            character will be ignored
        """
        from string import strip
        service = {'file' : fname}
        config = self.ssh.remotereadl(fname, dostrip=1, noempty=1, removecomments=1)
        problems = []

        if config == False:
            self.dprint("parseServiceConfig> error parsing config file [%s]: %s" % (fname,config))
            return False
        for line in config:
            if '=' in line:
                l = line.split("=")
                if len(l) > 2:
                    err =  '[%s] too many "=" characters in line' % line
                    self.dprint(err)
                    issue.append(err)
                    continue
                l = map(strip, l)
                quotes = [ "\"", "\'"]
                # leading quotes
                l = [ x[1:] if x[0] in quotes else x for x in l]
                # trailing quotes
                l = [ x[:-1] if x[-1] in quotes else x for x in l]
                kw, val = map(strip, l)
                # handle multiple values definition for a keyword
                # i.e. library service (each 'lib' kw defines a # library)
                if not kw in service.keys():
                    service[kw] = val
                else:
                    if not isinstance(service[kw], list):
                        service[kw] = [ service[kw] ]
                    # manage multiline comments
                    #if "\\n" in val: val = val.replace('\\n', '\n')
                    service[kw].append(val)
            else:
                err = '[%s] wrong format ("kw = value")' % line
                self.dprint(err)
                problems.append(err)
        return service, problems

    def installBinaryDISABLED(self, url=None, program='vina', tempdir=None, force=False):
        """
        if a custom url is provided, the program type must be specified as well
        """
        data_source = { 'vina' : {'url': 'http://vina.scripps.edu/download/autodock_vina_1_1_2_linux_x86.tgzxxx',
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

        status = { 'success': False, 'reason' : None }

        if url == None and program == None:
            self.dprint("Null request! link and program == None")
            return False

        info = data_source[program]
        # check if the file is already there
        for bin_name in info['binary']:
            self.dprint('Checking if binary [%s] already installed' % bin_name)
            if self.ssh.exists(bin_name):
                self.dprint('Found! aborting installation')
                return False

        # guessing the program link
        if not url:
            url = info['url']
            self.dprint("downloading %s [%s]" % (program, url))
        else:
            self.dprint("downloading from link: [%s]" % (url))

        # temp working dir and donwnload filename
        if tempdir == None:
            tempdir = os.getcwd()
        ## fname = os.path.basename(url) ! FRAGILE
        fname = url.rsplit('/', 1)[1]
        outfile = tempdir + os.path.sep + fname
        # downloading
        try:
            self.dprint('downloading file as [%s]...' % outfile)
            result = urllib.urlretrieve(url,outfile) # (fname, headers)
            installer, headers = result
        except:
            self.dprint('Error [%s]' % sys.exc_info()[1] )
            return False
        # extracting tar file
        result, source_files = hf.tarextract(tarfilename=installer, 
                                    filelist=info['binary'], outdir= tempdir)
        if result:
            dest_files = [ self.getBinPath() + os.path.basename(f) for f in source_files ]
            files = zip(source_files, dest_files)
            problems = self.ssh.putfiles( flist = files, mode=700) # <-executable
            if len(problems):
                self.dprint('Found problems:\n%s' % '\n'.join(problems) )
                return False
        return True

    def getQueueStatus(self):
        """
        this function should collect information on the 
        running jobs, the status of the resources (free nodes,
        etc..)

        it should spawn separate functions depending on the
        scheduler/res manager found
        """
        pass


    def registerJob(self, submission):
        """  register a job in self.history 
            and update the server history file
        """
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
            self.dprint("*TROUBLES AHEAD* : name already present [%s]... it should be unregistered first! Now is going to be overwritten." % jobname)
        self.history[prj][exp][jobname] = submission[prj][exp][jobname]
        # save date into remote history file
        self.saveHistory()

    def deleteJobRecord(self, name, prj=None, exp=None):
        """ remove a job record from the history dictionary
            if it is the only item in the experiment and the project,
            remove them too
        """
        self.dprint("Called with [%s|%s|%s]" % (prj, exp, name) )
        data = self.findJob(prj, exp, name)
        if data == ():
            self.dprint("deleting non-existent job... returning")
            return False
        prj, exp, name = data
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

    def unregisterJob(self, name, prj=None, exp=None, removefiles=True, kill=True):
        """ unregister jobs:
                1. kill pending (if any)
                2. delete files
                3. remove item from history
            from the SERVER and update the history file

            by default associated result files, if any, will be deleted 
            (removefiles option) and running jobs killed (kill option)
        """
        skip_list = ['killed', 'completed']
        self.dprint("called with [%s|%s|%s]" % (prj, exp, name) )
        report = { 'delfiles' : None, 'killjobs' : None}
        if removefiles or kill:
            if not self.updateJob(name=name, prj=prj, exp=exp) in skip_list:
                report['killjobs'] = self.killJob(name=name, prj=prj, exp=exp)
        if removefiles:
            report['delfiles'] = self.deleteJobData(name=name, prj=prj, exp=exp)
        self.deleteJobRecord(name, prj, exp)
        self.saveHistory()
        return True

    def deleteJobData(self, name, prj=None, exp=None):
        """ delete all files that belong to the job requested
        """
        self.dprint("called with [%s|%s|%s]" % (prj, exp, name))
        data = self.findJob(prj, exp, name)
        if data == (): return False
        data = self.getJobData(data)
        vsdir = data['vsdir']
        self.dprint("deleting vsdir [%s]" % vsdir)
        report = self.ssh.delfiles([vsdir])
        if len(self.history[prj][exp].keys()) == 1:
            # delete exp dir
            exp_dir = vsdir.rsplit('/', 1)[0]
            self.dprint("experiment [%s] will be now empty... deleting dir(%s)" % (exp, exp_dir))
            r = self.ssh.delfiles([exp_dir])
            self.dprint("delete result: %s" % r)
            if len(self.history[prj].keys()) == 1:
                # delete prj dir
                prj_dir = exp_dir.rsplit('/', 1)[0]
                self.dprint("experiment [%s] will be now empty... deleting dir(%s)" % (prj, prj_dir))
                r = self.ssh.delfiles([prj_dir])
                self.dprint("delete result: %s" % r)
        return report

    def killJob(self, name, prj=None, exp=None):
        """ try to kill running job """
        sched_func = { 'pbs' : self.killPbsJob,
                       'sge' : self.killSgeJob,
                     }
        data = self.findJob(prj, exp, name)
        if data == (): # killing unknown job
            return False
        data = self.getJobData(data)
        jobid = data['jobid']
        vsdir = data['vsdir']
        sched = self.getScheduler()
        return sched_func[sched](jobid = jobid, vsdir=vsdir)


    def killSgeJob(self, jobid, vsdir):
        """ kill SGE jobs
            jobid is a list of job ids from the submission
        """
        jobid.reverse() # to remove the collector first
        to_kill = " ".join(jobid)
        cmd = 'qdel %s ; touch %s/.killed'
        cmd = cmd % ( to_kill, vsdir)
        report = self.ssh.execmd(cmd)
        return report

    def killPbsJob(self, jobid, vsdir):
        """ kill PBS jobs
            jobid is a single PID of the submitter
        """
        submitting = False
        submit_f = vsdir + '/' + '.submitting'
        kill_submit = [ """touch %(vsdir)s/.stopsubmission""",
                        """kill -9 %(jobid)s""",
                        """touch %(vsdir)s/.killed""",
                        """rm -fr %(submit_f)s""",
                        ]
        # check the submitter and kill it if necessary
        if self.ssh.exists(submit_f):
            submitting = True
            cmd = ";".join(kill_submit)
            cmd = cmd % {'vsdir' : vsdir, 'jobid' : jobid[0], 'submit_f': submit_f }
            report = self.ssh.execmd(cmd)
            if report == False:
                self.dprint("Problems trying to kill-9 the submitter")
                return False
            stdout, stderr = report
            if len(stderr):
                self.dprint("Errors found: %s" % stderr)
                return False
        jid = self.checkJid(vsdir)
        if not jid:
            self.dprint("\"You're killing a dead man!\" - Francesco Ferruzzi [no JID for you]")
            return True
        cmd = 'qdel %s ; touch %s/.killed'
        cmd = cmd % ( jid, vsdir)
        report = self.ssh.execmd(cmd)
        return report


    def getJobStatus(self, jobid):
        """ retrieve scheduler info (if any) about the job
            vsdir is optional for sge, but required for pbs
        
        """
        sched = self.getScheduler()
        if sched == 'pbs' : 
            self.dprint("using PBS scheduler control")
            return self.pbsQstat(jobid)
        elif sched == 'sge': 
            self.dprint("using SGE scheduler control")
            return self.sgeQstat(jobid)
    
    def updateJobHistory(self, name, prj=None, exp=None):
        """ update job status and save it in history"""
        status = self.updateJob(name=name, prj=prj, exp=exp)
        if not status == 'unknown job':
            self.history[prj][exp][name]['status'] = status
            self.saveHistory()

    def updateJob(self, name, prj=None, exp=None):
        sched_func = { 'pbs' : self.updateJobPbs,
                       'sge' : self.updateJobSge,
                     }
        sched = self.getScheduler()
        return sched_func[sched](name=name, prj=prj, exp=exp)

    def updateJobSge(self, name, prj=None, exp=None):
        """ update job status """
        self.dprint("called with  P[%s] E[%s] V[%s]" % (prj, exp, name) )
        data = self.findJob(prj, exp, name)
        if data == ():
            return "unknown job"
        data = self.getJobData(data)
        # check if it has been deleted
        vsdir = data['vsdir']
        if not self.ssh.exists(vsdir):
            return 'deleted'
        # check if it has been killed
        if self.isjobkilled(name, prj=prj, exp=exp):
            return 'killed'
        # get job status
        total_status = []
        for j in data['jobid']:
            total_status.append( self.getJobStatus(j))
        self.dprint("the scheduler reported the following statuses : %s" % total_status)
        # no jobs left running
        if total_status == ['completed'] * len(data['jobid']):
            # no jobs are running, but either ".collecting" 
            # found or no collection started/ended
            suspicious = ['unknown', 'collecting']
            check = self.isjobcollecting(name, prj=prj, exp=exp)
            if check in suspicious:
                self.dprint("there are no jobs pending, the collector check returned [%s] (\"It's dead, Jim!\")" % check ) 
                return 'killed'
        # all jobs still queued
        if total_status == ['queued'] * len(data['jobid']):
            return 'queued'
        # one job == collecting
        if len(total_status) == 1:
            #coll_status = self.isjobcollecting(name)
            if self.isjobcollecting(name) == 'collecting':
                return 'collecting'
        # running
        if 'running' in total_status:
            # check completion level
            completion = self.completionLevel(name)
            if completion == 'error':
                #return 'error (completion check)' 
                # FIXME this should be more informative?
                return float(0)
            c =  hf.percent(completion, data['total'])
            if c > 100:
                self.dprint("caught count glitch! completion[%2.3f%%]" % c)
                c = 99
            return float(c)
        if 'held' in total_status:
            if total_status == ['held'] * len(data['jobid']):
                return 'held'
            else:
                return 'held/queued'
        return 'completed'

    def isPbsSubmitting(self, p,e,n):
        """ check if the PBS submitter script is still running
            a job could be:
                - PID-alive             (True)
                - PID-dead, fs-updating (True)
                - PID-dead, fs-updated  (False)

        In the last case, it is important to return False
        because it is possible that if the FS has not been 
        updated, the checkings for the collection will fail 
        as well.
        """
        data = self.findJob(p, e, n)
        data = self.getJobData(data)
        vsdir = data['vsdir']
        jobid = data['jobid'][0]
        submit_f = vsdir + '/' + '.submitting'
        submit_trace = self.ssh.exists(submit_f)
        alive = self.isPbsSubmitAlive(jobid)
        self.dprint("Tracing file is [%s]:[%s]" %(submit_trace, submit_f))
        self.dprint("PID checking is [%s]:[%s]" %(alive, jobid))
        print "\n\nTracing file is [%s]:[%s]" %(submit_trace, submit_f)
        print "\n\nPID checking is [%s]:[%s]" %(alive, jobid)

        return submit_trace or alive

    def isPbsSubmitAlive(self, jobid):
        """ check if the submitting process is
            still alive
        """
        #data = self.findJob(p,e,n)
        self.dprint("Called with jobid[%s]" % jobid)
        print "Called with jobid[%s]" % jobid
        #cmd = "ps -p %s 1>/dev/null ; echo $?"
        cmd = "ps --no-headers -p %s"
        cmd = cmd % jobid
        report = self.ssh.execmd(cmd)
        if not report:
            return False
        stdout, stderr = report
        #alive = int(stdout[-1])
        alive = len(stdout)
        if alive > 0:
            return True
        return False


    def updateJobPbs_OLD(self, name, prj=None, exp=None):
        """ update job status 
            the status of a PBS job is complex :

                 | PID | JID | .submitting | .collecting | .collected 
  ----------------------------------------------------------------------
  pbsSubmit.sh   |  1  |  0  |     1       |    0        |     0
   job.j         |  1  |  1  |     1       |    0        |     0
   collector (S) |  0  |  1  |     0       |    1        |     0
   collector (E) |  0  |  0  |     0       |    0        |     1

            the (apparent) most efficient way of checking the status
            is to to from bottom-right to top-left (toward more expensive
            checkings like % of completion)
        """
        self.dprint("called with  P[%s] E[%s] V[%s]" % (prj, exp, name) )
        data = self.findJob(prj, exp, name)
        if data == ():
            return "unknown job"
        data = self.getJobData(data)
        vsdir = data['vsdir']
        # check if it has been deleted
        if not self.ssh.exists(vsdir):
            return 'deleted'
        # check if it has been killed
        if self.isjobkilled(name):
            return 'killed'
        # is the job collecting/done?
        check = self.isjobcollecting(name, prj=prj, exp=exp)
        if check == 'done':
            return 'completed'
        if check == 'collecting':
            return 'collecting'
        # state in wich no collection has been performed...
        submitting = self.isPbsSubmitting(prj,exp,name)
        if not submitting:
            self.dprint("no job is submitting... giving collection another chance...")
            check = self.isjobcollecting(name)
            if check == 'done':
                return 'completed'
            if check == 'collecting':
                return 'collecting'
            if self.checkJid(vsdir):    
                m = ('possible intermediate state where collector '
                     'is taking place with no updates (yet) but '
                     'there\'s still a JID pending...'
                     'returning [collecting]')
                return 'collecting'
            self.dprint("no submission, no collection running or done...(\"It's dead, Jim!\")")
            # state in wich no collection has been performed...
            return 'dead?'
        jid = self.checkJid(vsdir)
        if jid == False:
            self.dprint('no JID available! possible troubles ahead')
            return 'missing JID!'
        status = self.getJobStatus(jid)
        self.dprint("the scheduler reported the following status : %s" % status)
        #print "\t\t\tthe scheduler reported the following status : %s" % status
        if status == 'queued':
            return 'queued'
        if self.isjobcollecting(name, prj=prj, exp=exp):
            #coll_status = self.isjobcollecting(name)
            if self.isjobcollecting(name) == 'collecting':
                return 'collecting'
        # running
        if status == 'running' or submitting:
            # check completion level
            completion = self.completionLevel(name, prj = prj, exp=exp)
            if completion == 'error':
                #return 'error (completion check)' 
                # FIXME this should be more informative?
                return float(0)
            c =  hf.percent(completion, data['total'])
            if c > 100:
                self.dprint("caught count glitch! completion[%2.3f%%]" % c)
                c = 99
            return float(c)
        if status == 'held':
            return 'held'
        if submitting:
            print "REPORTED STILL SUBMITTING"
            return 'submitting'
        else:
            return 'completed'


    def updateJobPbs(self, name, prj=None, exp=None):
        """ update job status 
            the status of a PBS job is complex :

                 | PID | JID | .submitting | .collecting | .collected 
  ----------------------------------------------------------------------
  pbsSubmit.sh   |  1  |  0  |     1       |    0        |     0
   job.j         |  1  |  1  |     1       |    0        |     0
   collector (S) |  0  |  1  |     0       |    1        |     0
   collector (E) |  0  |  0  |     0       |    0        |     1

            the (apparent) most efficient way of checking the status
            is to to from bottom-right to top-left (toward more expensive
            checkings like % of completion)
        """
        # known job
        self.dprint("called with  P[%s] E[%s] V[%s]" % (prj, exp, name) )
        data = self.findJob(prj, exp, name)
        if data == ():
            return "unknown job"
        data = self.getJobData(data)
        vsdir = data['vsdir']
        # check if it has been deleted
        if not self.ssh.exists(vsdir):
            return 'deleted'
        # check if it has been killed
        if self.isjobkilled(name):
            return 'killed'
        # the job is alive and well...
        submitting = self.isPbsSubmitting(prj,exp,name)
        if submitting:
            # pbs scheduler check
            jid = self.checkJid(vsdir)
            if jid == False:
                self.dprint('no JID available! possible troubles ahead')
                return 'missing JID!'
            status = self.getJobStatus(jid)
            self.dprint("the scheduler reported the following status : %s" % status) 
            # r, q, h
            # check if some work has been done so far..
            completion = self.completionLevel(name, prj = prj, exp=exp)
            if completion == 'error':
                #return 'error (completion check)' 
                # FIXME this should be more informative?
                return float(0)
            c =  hf.percent(completion, data['total'])
            if c > 100:
                self.dprint("caught count glitch! completion[%2.3f%%]" % c)
                c = 99
            if c == 100 and status not in ['running', 'completed']:
                c = 99
                #  catch a state in which a job has been deferred
                #  and the collector hasn't been launched by 
                #  yet...
            return float(c)            
        else:
            collecting = self.isjobcollecting(name, prj=prj, exp=exp)
            if collecting == 'collecting':
                return 'collecting'
            elif collecting == 'done':
                return 'completed'
        print "\n\n\n\t============== SOMETRHING UNCATCHED HERE! WRONG?"
        return "UNDEFINED STATE! submitting[%s]" % submitting

    def isjobkilled(self, name, prj=None, exp=None):
        """ return boolean if job has been killed"""
        data = self.findJob(prj, exp, name)
        if data == (): return True
        data = self.getJobData(data)
        # check if the job has been killed
        fname = data['vsdir'] + '/' + '.killed'
        if self.ssh.exists(fname):
            return True
        return False

    def isjobcollecting(self, name, prj=None, exp=None):
        """ return boolean if job data is getting collected by tar"""
        data = self.findJob(prj, exp, name)
        if data == (): return False 
        data = self.getJobData(data)
        fname = data['vsdir'] + '/' + '.collecting'
        if self.ssh.exists(fname):
            return 'collecting'
        fname = data['vsdir'] + '/' + '.collected'
        if self.ssh.exists(fname):
            return 'done'
        return 'unknown'


    def pbsQstat(self, jobid):
        """ check the status of a job
                "job_state = R"
        """
        kw = 'job_state'
        cmd = """qstat -f  %s | grep %s""" % (jobid, kw)
        report = self.ssh.execmd(cmd)
        if not report: 
            print "ERROR"
            return 'error'
        stdout, stderr = report
        if len(stdout):
            self.dprint("qstat output [%s]" % stdout[0])
            status = stdout[0].split("=",1)[1].strip()
            if status == 'R':
                return 'running'
            elif status == 'Q' or status == 'W':
                return 'queued'
            elif status == 'H':
                return 'held'
        else:
            return 'completed'
        return 'completed'

    def checkJid(self, vsdir):
        """ read the job id of the latest PBS job
            submitted by the PBS submitter
        """
        jid_f = vsdir + '/' + '.jid'
        if self.ssh.exists(jid_f):
            fp, sftp = self.ssh.openfile(jid_f)    
            jid = fp.readlines()[0].strip()
            fp.close()
            sftp.close()
            return jid
        return False

    def checkPid(self, vsdir):
        """ read the job id of the latest PBS job
            submitted by the PBS submitter
        """
        pid_f = vsdir + '/' + '.pid'
        if self.ssh.exists(pid_f):
            fp, sftp = self.ssh.openfile(pid_f)    
            pid = fp.readlines()[0].strip()
            fp.close()
            sftp.close()
            return pid
        return False

    def sgeQstat(self, jobid):
        """ """
        cmd = """qstat | grep  %s |awk '{print $5}'""" % jobid
        report = self.ssh.execmd(cmd)
        if not report: return 'error'
        stdout, stderr = report
        if len(stdout):
            self.dprint("qstat output [%s]" % stdout[0])
            #status = stdout[0].split("=",1)[1].strip()
            status = stdout[0].strip()
            status.lower()
            if status == 'r':
                return 'running'
            elif status == 'q':
                return 'queued'
        else:
            return 'completed'

    def completionLevel(self, jobid, prj=None, exp=None):
        """ try to calculate completion level"""
        data = self.findJob(prj, exp, jobid)
        if data == (): return True
        data = self.getJobData(data)
        cmd = """wc -l %s/%s""" % (data['vsdir'], data['statusfile'])
        self.dprint("cmd> %s" % cmd)
        report = self.ssh.execmd(cmd)
        self.dprint("report: ", report)
        if not report: 
            return 'error'
        stdout, stderr = report
        if len(stdout):
            count = int(stdout[0].split(" ", 1)[0])
            self.dprint("jobs completed [%d]" % count)
            return count
        return 'error'
            
    def downloadResult(self, name, destpath, prj=None, exp=None, bg=True, cb=None):
        """ retrieve the tar file with results""" 
        self.dprint("name[%s] destpath[%s] bg[%s]" % (name, destpath, bg) )
        data = self.findJob(prj, exp, name)
        if data == (): return False
        data = self.getJobData(data)
        tarfile = "%s.tar.gz" % name
        source = "%s/%s" % ( data['vsdir'], tarfile)
        #dest = "%s%s%s" ( destpath, os.sep, tarfile)
        if not self.ssh.exists(source):
            self.dprint("tar file [%s] does not exist, download skipped" % source )
            return False
        return self.transfer.downloadBigFile(source, destpath, bg, cb) 
    
    def updateDownloadStatus(self):
        """ call the download manager and ask for the status"""
        return self.transfer.updateDownloadBigFile()

    def stopDownload(self):
        """ halt an ongoing download"""
        self.transfer.stop()


    def getMasterLog(self, name, prj=None, exp=None):
        """ retrieve the content of the master log file"""
        # scheduler_master.log
        data = self.findJob(prj, exp, name)
        if data == (): return False
        data = self.getJobData(data)
        fname = data['vsdir'] + '/' + data['masterlog']
        opening = self.ssh.openfile(fname)
        if isinstance(opening, tuple):
            fp, sftp = opening
            lines = fp.readlines()
            fp.close()
            sftp.close()
            return lines
        return opening

#############################


class RaccoonLocalServer(DebugObj):

    def __init__(self, debug=True):
        """we need to test the architecture first!"""
        pass 


    def getHomePath(self):
        try:
            from win32com.shell import shellcon, shell            
            homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
 
        except ImportError: # quick semi-nasty fallback for non-windows/win32com case
            homedir = os.path.expanduser("~")
        
##############################


class RaccoonOpalServer(DebugObj):

    def __init__(self, debug=True):
        """we need to test the architecture first!"""
        pass 




if __name__ == '__main__':
    print "START TESTING"



