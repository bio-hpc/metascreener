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


import paramiko as pmk
import socket
#import os
import sys
import time
from datetime import datetime
import errno
import Queue
import threading
import tarfile
import os
from DebugTools import DebugObj
import sys
from CADD.Raccoon2 import HelperFunctionsN3P as hf

# NOTES
# http://jessenoller.com/2009/02/05/ssh-programming-with-paramiko-completely-different/


# when transferring files, spawn a thread by opening a connection
# to the server and letting it run on the background...



class RaccoonSshClient(DebugObj):
    """provide the basic features for using a remote SSH server
       (i.e. linux cluster, remote machines, etc...)

        openconnection()    initialize the connection (self.connection)
        closenConnection()  close the connection (self.connection=None)
        execmd()           execute remote commands
        getfiles()          copy remote files locally
        putfiles()          copy local files remotely
        delfiles()          delete remote files/dirs
        openfile()          open a remote file (return pointer)
        listdir()           return the files present in the path
        

        NOTES: basic operation functions will normalize the path (self.normpath):
            - self.openfile
            - self.exists

    """
    def __init__(self, address=None, username=None, password=None, name='RaccoonSshClient_server', 
                debug=False, usesyshostkeys=True, autoaddmissingkeys=True, 
                pkey=None, autoconnect=False):
        
        DebugObj.__init__(self, debug)

        self.autoaddmissingkeys = autoaddmissingkeys
        self.usesyshostkeys = usesyshostkeys
        self.address = address
        self.username = username
        self.password = password
        self.name = name
        self.pkey = pkey
        self.connection = None
        self.connectiontime = None
        if autoconnect:
            self.openconnection()

        #pmk.util.log_to_file("paramiko_raccoon_connection.log")


    def setserver(server={}, autoconnect=False):
        # reset the server parameters...
        # FIXME complete or remove...
        print "\n\n\n************** WARNING! INCOMPLETE FUNCTION!!!! CALL FOR HELP!!! ****"
        print "THIS FUNCITION SHOULD BE REMOVED IN THE FINAL VERSION SINCE IT IS NOT USED"
        if not self.connection == None:
            self.closeconnection()
        keys = server.keys()
        if 'address' in keys:
            self.address = server['address']
        if 'username' in keys:
            self.username = server['username']
        if 'password' in keys:
            self.password = server['password']
        if 'pkey' in keys:
            self.pkey = server['pkey']
        if autoconnect:
            self.openconnection()

    def openconnection(self):
        """
        set the current server to be 'servername' and 
        initialize the connection (username, passwd)

        the connection start time is stored in self.connectiontime

        """
        if not self.connection == None:
            self.dprint('connection already open')
            return 1
        self.dprint("opening a new connection", new=1)
        conn = pmk.SSHClient()
        if self.autoaddmissingkeys: # 
            conn.set_missing_host_key_policy(pmk.AutoAddPolicy())

        # FIXME this should be configurable
        options = {'port': 22} 
        if self.usesyshostkeys:     # .ssh/authorized_keys
            try:
                self.dprint("using SYSTEM HOST KEYS")
                conn.load_system_host_keys()
            except IOError:
                e = sys.exc_info()[1]
                self.dprint("No keys found [ %s ]" % e)
                err = 'keys not available in [ %s ]' % e
                err_o = IOError
        elif not self.pkey == None:
            options['key_filename'] = self.pkey
            self.dprint("using user defined HOST KEY [%s]" % self.pkey)
        else:
            self.dprint("trying password [%s]" % self.password)
            options['password'] = self.password
        err = 'Connection not open (UNKNOWN ERROR)'
        shell = 'unk'
        shell_errors = ['none']
        try:
            conn.connect(hostname=self.address, username=self.username, **options) # password=self.password)
            # NOTE FRAGILE SHELL TEST 
            # this test is used for fragile shells (i.e. csh) to trigger 
            # SSHException(EOF) if there are errors in the rc files (i.e.
            # .cshrc)
            cmd = "echo $SHELL"
            stdin_raw, stdout_raw, stderr_raw = conn.exec_command(cmd)

            shell_errors = stderr_raw.readlines()
            shell = stdout_raw.readlines()[0].strip()
            stdin_raw.close()
            stdout_raw.close()
            stderr_raw.close()
            sftp = conn.open_sftp()
            sftp.close()
            # FRAGILE SHELL TEST /END
            self.connection = conn
            self.connectiontime = datetime.now()
            err = None
        except pmk.BadHostKeyException:
            """if the server's host key could not be verified"""
            err = "host key could not be verified (%s)" % sys.exc_info()[1]
            err_o = pmk.BadHostKeyException
        except pmk.AuthenticationException:
            """ if authentication failed"""
            err = "error in the authentication (%s)" % sys.exc_info()[1]
            err_o = pmk.AuthenticationException
        except pmk.SSHException:
            """ if there was any other error connecting or establishing an SSH session"""
            err = "error in establishing SSH session (%s)" % sys.exc_info()[1]
            if "EOF" in err:
                if len(shell_errors):
                    err += ('\n\nThe following errors have been reported '
                            'by the remote shell:\n\n'
                            '====[ %s ]====\n'
                            '\n%s\n================\n'
                            '\nConnection failure could be due to errors in setting '
                            'files (i.e. ".*rc", ".login" files) of the remote shell.'
                            ) % (shell, '\n'.join(shell_errors))
            err_o = pmk.SSHException
            
        except socket.error:
            """ a socket error occurred"""
            err = "socket error (%s)" % sys.exc_info()[1]
            err_o = socket.error
        except:
            """ undefined error"""
            err = "unknown error (%s)" % sys.exc_info()[1]
            err_o = None

        finally:
            self.dprint("SHELL [%s]" % shell)
            if len(shell_errors):
                for i in shell_errors:
                    self.dprint("SHELL ERROR> %s" %i)
            if err == None:
                self.dprint("[ connection open ]")
                self.expanduservar()
                return 1
            else:
                print "openconnection> an error occurred : ", err
                self.dprint("connection not opened, error[%s]" % err)
                return err, err_o

    def expanduservar(self):
        """ resolve the "~" expanding it to the user home fullpath"""
        self.dprint("set the uservar '~'...")
        cmd = 'echo ~'
        out, err = self.execmd(cmd)
        uservar = out[0]
        self.dprint("found [%s]")
        self.uservar = uservar


    def closeconnection(self):
        """ close connection and reset the connection time to None """
        self.dprint("closing open connection...", new=1)
        if not self.connection == None:
            self.connection.close()
            self.connection = None
            self.connectiontime = None
            self.dprint("closed.")
            self.uservar = None
            return
        self.dprint("no open connection to close...")


    def execmd(self, command, auto=False, getlines=True, dostrip=True, full = False, forceclose=False):
        """ execute command on remote server and return stdout and stderr
            as lists
        
            getlines: if true, lists instead of pointers are returned
            dostrip : (if getlines) lines are stripped
            full    : return stdin, stdout, stderr [default: stdout, stderr]
        """
        self.dprint('COMMAND:[%s]' % command, new=1)
        if self.connection == None:
            print "No connection"
            return False
        try:
            self.dprint("executing [%s]..." % command)
            stdin_raw, stdout_raw, stderr_raw = self.connection.exec_command(command)
            if forceclose:
                try:
                    print "Closing..."
                    stdin_raw.write('exit')
                    stdin_raw.close()
                except: 
                    print "CATCHED SOMETHING", sys.exc_info()[1]
                    pass
                self.dprint("DONE (force closing)")
                return  stdout_raw, stderr_raw 
            self.dprint("DONE")
        except:
            print "excmd> ERROR! [%s]" % (sys.exc_info()[1])
            return False
        if getlines and not forceclose:
            #stdin = stdin.readlines()
            stdout = stdout_raw.readlines()
            stderr = stderr_raw.readlines()
            stdout_raw.close()
            stderr_raw.close()
            if dostrip:
                #from string import strip
                stdout = [x.strip() for x in stdout]
                stderr = [x.strip() for x in stderr]
        if full:
            return (stdin_raw, stdout_raw, stderr_raw)
        return (stdout, stderr)

    def normpath(self, dirname):
        """ normalize the path by removing the user tildes if present 
           
            TODO: check if it is necessary to expand it? ("~" -> "/home/userx") ?

            fragile!?

            this should be safer:

            dirname = self.execmd("echo %s" % dirname, getlines=1)[0][0]
        """
        #return self.execmd("echo %s" % dirname, getlines=1)[0][0] # XXX VERY SLOW!
        if dirname.startswith("~/"):
            dirname = self.uservar+'/'+dirname[2:]
        return dirname


    def getfiles(self, flist=[], auto=True):
        """
        get fname from server 

        flist = [  ['source1', 'dest1'], 
                   ['source2', 'dest2'], 
                   ...
                ]
        """
        if self.connection == None and not auto:
            self.dprint(" no connection open on the server [%s]" % self.server_info['address'])
            return
        self.openconnection()
        sftp = self.connection.open_sftp()
        problems = []
        for f in flist:
            try:
                sftp.get(self.normpath(f[0]), self.normpath(f[1]))
            except:
                problems.append((f, sys.exc_info()[1]))
        sftp.close()
        return problems

        
    def putfiles(self, flist=[], mode=None, auto=True):
        """
        copy file on the server
        flist = [ [ source1, dest1], [source2, dest2], ... ]

        if optional 'mode' is provided, the file attributes will be
        changed as 'chmod mode filename'

        NOTE: if a remote directory is specified, it must exist!

        """

        if self.connection == None and not auto:
            print "putfiles> no connection open on the server [%s]" % self.server_info['address']
            return
        self.openconnection()
    
        sftp = self.connection.open_sftp()
        problems = []
        for f in flist:
            try:
                sftp.put(self.normpath(f[0]), self.normpath(f[1]))
            except:
                problems.append([f, sys.exc_info()[1]])
        sftp.close()

        if not mode == None:
            files = [ self.normpath(x[1]) for x in flist]
            files = " ".join(files)
            cmd = 'chmod %s %s' % (mode, files)
            self.execmd(cmd)
        return problems

    def makedir(self, dirname, mode=711, auto=True):
        """ probably not very efficient recursive hack to 
            allow parent creation when making a dir
        """
        # XXX
        # XXX what about executing the mkdir -p command and thazzit?
        # XXX

        dirname = self.normpath(dirname)
        cmd = """mkdir -m %s -p %s""" % (mode, dirname)
        cmd = """mkdir -p %s""" % ( dirname)
        report = self.execmd(cmd, getlines=True)
        if report == False:
            print "makedir> error in creating directory"
            return
        stdout, stderr = report
        self.dprint("STDOUT> %s" % stdout)
        self.dprint("STDERR> %s" % stderr)
        if len(stderr) == 0:
            self.dprint("no errors, success")
            return True
        else:
            self.dprint("ERRORS!")
            return stderr
        
        """
        forbidden = ['~', '/', None]
        dirname = self.normpath(dirname)
        if self.connection == None and not auto:
            print "makeDir> no connection open on the server [%s]" % self.server_info['address']
            return
        self.openconnection()

        sftp = self.connection.open_sftp()
        if '/' in dirname:
            parent = dirname.rsplit('/', 1)[0]
        else:
            parent = None
        if (not parent in forbidden) and (not self.exists(parent)):
            # XXX WARNING! FRAGILE HERE XXX #
            print "parent doesn't exists [%s]" % parent
            self.makedir(parent)
        sftp.mkdir(dirname, mode=mode)
        sftp.close()
        """

    def delfiles(self, flist=[], auto=True):
        """ delete files in the remote location 
            flist can contain both files and directories

            NOTE: better user self.execmd( 'rm -fr ...') ?
        
        """

        if self.connection == None and not auto:
            print "delfiles> no connection open on the server [%s]" % self.server_info['address']
            return
        self.openconnection()

        sftp = self.connection.open_sftp()
        problem = None
        flist = ' '.join(["%s" % x for x in flist ])
        try:
            cmd = 'rm -fr %s' % flist
            out, err = self.execmd(cmd)
        except:
            problem = "Error executing command. Cmd[%s], Error[%s]" % (cmd, sys.exc_info()[1])
        if len(err):
            problem = "Error executing command. Cmd[%s], Error[%s]" % (cmd, sys.exc_info()[1])
        sftp.close()
        return problem


    def openfile(self, fname, mode='r', bufsize=-1, auto=True):
        """
        open a remote file and 
        return the filepointer
        """
        fname = self.normpath(fname)
        self.dprint("Opening (normalized) filename [%s]" % fname)
        if self.connection == None:
            if not auto:
                print "openfile> no connection open on the server [%s]" % self.server_info['address']
                return
        else:
            self.openconnection()

        sftp = self.connection.open_sftp()
        try:
            return (sftp.open(fname, mode=mode, bufsize=bufsize), sftp)
        except:
            return sys.exc_info()[1]


    def touchfile(self, fname, auto=True):
        """
        touch a file on the remote server
        """
        fname = self.normpath(fname)
        out = self.openfile(fname, 'a')
        try:
            out[0].close()
            out[1].close()
            return True
        except:
            return out
            
    def remotereadl(self, fname, dostrip=1, noempty=1, removecomments=1):
        """ read a remote file and return lines
         
            by default, lines are stripped
        """
        from string import strip
        out = self.openfile(fname)
        if not type(out) == type(()):
            print "remotereadl> Error reading file [%s] : %s" % (fname, out)
            return False
        fp, sftp = out
        lines = fp.readlines()
        fp.close()
        sftp.close()
        if removecomments:
            #lines = [ l for l in lines if not l.startswith('#') ]
            # this removes comments more efficiently
            lines = [ l.split("#", 1)[0] for l in lines]
        if noempty:
            lines = [ l for l in lines if l.strip() ]
        if dostrip:
            lines = map(strip, lines)
        return lines

    def remotewritel(self, fname, _list, mode='a', addnl=1):
        """ write a list on a remote file
            by default new lines are added unless 'addnl=0' is specified
            also, data is appended to existing files unless
            mode='w' is specified
        """
        nl=''
        if addnl: nl='\n'
        out = self.openfile(fname)
        if not type(out) == type(()):
            print "remotewritel> Error opening file [%s, mode:%s] %s" % (fname, mode, out)
            return False
        fp, sftp = out
        for l in _list:
            fp.write( l+nl )
        fp.close()
        return True


    def exists(self, path, auto=True, info=False):
        """Return True if the remote path exists
        """
        path = self.normpath(path)
        if self.connection == None and not auto:
            print "openfile> no connection open on the server [%s]" % self.server_info['address']
            return
        self.openconnection()
        try:
            sftp = self.connection.open_sftp()
            x = sftp.stat(path)
            sftp.close()
            self.dprint("File [%s] exists: [%s]" % (path, x))
        except IOError, e:
            if e.errno == errno.ENOENT:
                self.dprint("File [%s] not found" % path)
                return False
            raise
        else:
            if info:
                prop = { 'mode' : x.st_mode,
                         'size' : x.st_size,
                         'uid'  : x.st_uid,
                         'gid'  : x.st_gid,
                         'atime': x.st_atime,
                         'mtime': x.st_mtime,
                        }
                return prop
            return True

    def findcommand(self, command, which=True):
        """ test if an executable command can be found with is 
            full-path or can be found by the UNIX command 'which'. 
        """
        found = False
        if self.exists(command):
            found = command
        if not found and which:
            self.dprint("which requested")
            cmd = '''which "%s"''' % command
            report = self.execmd(cmd)
            if report == False:
                return False
            stdout, stderr = report
            self.dprint("STDOUT[%s]" % stdout)
            self.dprint("STDERR[%s]" % stderr)
            if len(stdout):
                if not stdout[0] == '':
                    found = stdout[0]
                    if not ("not found" in found): 
                        # Rats! Csh, the shell from Hell returns
                        # the "command not found" as STDOUT...
                        self.dprint("Found binary => [%s]" % (stdout[0]))
                    else:
                        found = False
                else:
                    self.dprint("Impossible to find %s binary => [??]" % (command))
        #print "FINDCOMMAND>", found
        return found        


    def listdir(self, path):
        """ return the list of directories on the requested path """
        path = self.normpath(path)
        try:
            sftp = self.connection.open_sftp()
            ls = sftp.listdir(path)
            sftp.close()
            return ls
        except:
            return False

    def diskspace(self, path, human=True):
        """ check available disk space in the requested
            location

            by default the space is reported in
            human-readable format
        """
        suffixd = { 'P' : ' petabytes (a lot!)',
                    'T' : ' terabytes',
                    'M' : ' megabytes',
                    'K' : ' kilobytes',
                  }
        unk = ' unknown [furlong per forthnight?]'
        if human: hopt = '-h'
        else: hopt = ''
        cmd = """df %s %s | tail -1 | awk '{print $2}'""" % (hopt,path)
        report = self.execmd(cmd)
        if report == False:
            print "diskavail> error in the connection"
            return False
        stdout, stderr = report
        if len(stderr):
            print "diskavail> Errors encountered:\n%s\n" % "\n".join(stderr)
        if not len(stdout):
            print "diskavail> Empty stdout returned."
            return False
        space = stdout[0]
        if human:
            suffix = suffixd.get(space[-1], unk)
            space = space[:-1] + suffix
        return space


class ThreadedOperation: #(threading.Thread):
    """Basic class defining threaded operations

    it shuold be used to submit threads of given functions
    providing a queue mechanism for each one of them

    """
    def __init__(self, queue_mode = 'lifo'):
        #threading.Thread.__init__(self)
        if queue_mode == 'lifo':
            self.queue = Queue.LifoQueue
        elif queue_mode == 'fifo':
            self.queue = Queue.Queue

        self.jobs = []

    def run(self, func, args={}):
        self.pax
        pass


    def stop(self):
        self._STOP = False
        self._completed = False
        pass




class FileMule(DebugObj):
    """ Class to handle non-blocking transfers of large number of files/dirs
        such as ligand libraries with nested sub-dirs. It supports GZ and BZ2
        compressions.

        The transfer opens remote tar writing [or reading] pipes and transfer 
        the files through it, letting the remote tar process to create [or read]
        all files and dirs.
        The transfer mimics the following shell commands:

        WRITING:
            local> tar cf - $LOCAL_DIR | ssh "cd $REMOTE_DIR; tar xf -"

        READING:
            local> ssh "tar cf - $REMOTE_DIR" | tar xf -

        It can be spawned from a connection that is already open
        by passing the ssh client to it.
        
        It has an internal counter to be used to check status when it is 
        executed within its own thread (i.e. in a GUI):

        
            import threading
            ssh = RaccoonSshClient( address, username, password)
            transfer = FileUploader( parent = ssh, files_list, path='remote_path',
                tarname = 'temptar', compression = 'gz')

            thread = threading.Thread(target = transfer.upload)
            thread.start()

            status = transfer.progress(percent=True)


        
        NOTE: autoconnect is True by default (different than RaccoonSshclient
              default).
              
    """
    def __init__(self, ssh=None, address=None, username=None, password=None, name='RaccoonSshClient_server', 
            debug=False, usesyshostkeys=True, autoaddmissingkeys=True, pkey=None, autoconnect=True):
            ## ,  # XXX
            ## files=None, path = None, targetname = 'tmpfile', compression='gz'):

        # files, path, targetname and compression shuold be 
        # moved to the respective functions upload() and download()

        DebugObj.__init__(self, debug)

        if ssh:
            self.dprint("parent SSH connection provided: [%s]" % ssh)
            self.ssh = ssh
        else:
            self.dprint("open new SSH connection...")
            self.ssh = RaccoonSshClient(address, username, password, name, debug, 
                usesyshostkeys, autoaddmissingkeys, pkey, autoconnect)
            self.dprint("SSH connection open [%s]" % self.ssh)

        self._ready = False
        self._counter = 0.
        self._total = 0.
        self._STOP = False
        self._running = False
        self.pending = None
        self._status = { 'completed' : False, 'error': None }

        self.test()

    def test(self):
        """ check that requirements to transfer the files are satisfied"""
        self._ready=False
        if self._checkTar():
            self.dprint("tar test passed")
            self._ready = True
        else:
            self.dprint("test failed at tar.")

    def _checkTar(self):
        """check if the server has tar installed"""
        return self.ssh.findcommand("tar", which=True) 

    def stop(self):
        """ set the STOP variable to true, so running operations
            that check it can stop
        """
        if not self.checkPending():
            return
        msg = "transfer stop requested"
        self.dprint(msg)
        self._status['error'] = msg
        self._STOP = True
        self._completed = False

    def close(self):
        self._running = False
        self._STOP = False
        self.tarfile.close()
        self._status = {'completed' : False, 'error' : 'stopped'} 


    def upload(self, files=[], remotedestpath='.', compression='gz', bg=False): #, date=True):
        """ transfer files to a remote location

            this operation is designed to be threaded

            files = [ [ source_full_path_and_name, dest_relative_path_and_name ],
                   ]

            TODO investigate if files must be provided as pair (to avoid long paths
             and so on...)
        """
        if bg == False:
            self._upload_tar(files, remotedestpath, compression)
        else:
            self.pending = threading.Thread(target = self._upload_tar, args = ( files, remotedestpath, compression))
            self.pending.start()           

    def _upload_tar(self, files=[], remotedestpath='.', compression='gz'):
        # check if the destination path exists, otherwise exit..
        if remotedestpath == None:
            self.dprint("ERROR: Remote path not specified, returning")
            self._status = {'completed' : False, 'error' : 'remote path not specified'}
            return False
        if not self.ssh.exists(remotedestpath):
            self.dprint("Remote path [%s] do not exist, returning" % remotedestpath)
            self._status = {'completed' : False, 'error' : 'remote path does not exist'}
            return False
        self._status['completed'] = False
        self._counter = 0
        self._total = len(files)
        if compression == None :
            opt = ''
            mode = 'w'
        elif compression == 'gz' :
            opt = 'z'
            mode = 'w:gz'
        elif compression == 'bz2': 
            opt = 'j'
            mode = 'w:bz2'
        cmd = 'cd %s; tar %sxf -' % (remotedestpath, opt)
        #cmd = 'cd %s; tar %scf trap.tar' % (remotedestpath, opt)
        self._running = True
        self.dprint("command [%s]" % cmd)
        stdin, stdout, stderr = self.ssh.execmd(cmd, getlines=False, full=True)
        self.tarfile = tarfile.open(fileobj = stdin, mode=mode)
        for f in files:
            if self._STOP:
                self.dprint("Stop requested, halting")
                self.close()
                return
            infile, destfile = f
            destfile = self.ssh.normpath(destfile)
            self.dprint("Remote TAR writing src[%s] => dest[%s] %d" % (infile, destfile, self.progress(percent=1)) ),
            self.tarfile.add(infile, arcname=destfile)
            #self.tarfile.fileobj.flush()
            self._counter += 1
        self.tarfile.close()
        stdin.flush()
        # http://stackoverflow.com/questions/8052840/paramiko-piping-blocks-forever-on-read
        stdin.channel.shutdown_write()
        stdin.close()
        stdout.close()
        stderr.close()
        self._status = {'completed' : True, 'error' : None}
        self._running = False
        ### if date:
        ###     print "WRITE A DATE COMMAND LOG IN A FILE !!!"
        return True

    def checkPending(self):
        """check if a pending operation is pending"""
        if self.pending == None:
            return False
        pending = self.pending.isAlive()
        if not pending:
            self.pending = None
        return pending


    def downloadBigFile(self, source, destpath='.', bg=True, cb=None):
        """ manage the download of one single big result (tar) file """
        info = self.ssh.exists(source, info=True)
        if info == False:
            self.dprint("non-existent file [%s]", source)
            return False
        self._total = float(info['size']) # the size of the final file
        localname = source.rsplit("/", 1)[1]
        self._localfile = "%s%s%s" % ( destpath, os.sep, localname)
        self.download([source], destpath, compression=None, bg=bg, cb=cb)
        

    def updateDownloadBigFile(self):
        """ update download status of big files transfers"""
        if self.checkPending() == False:
            return 100.00
        #self._counter
        try:
            self.dprint("checking local size of [%s]" % self._localfile)
            curr_size = os.stat(self._localfile).st_size
            self.dprint(' found %s' % curr_size)
        except:
            self.dprint('file checking error [%s]' % sys.exc_info()[1] )
            curr_size = 0
        pc = hf.percent(curr_size, self._total)
        self.dprint("current size [%d/%d] : %2.3f%%" % (curr_size, self._total, pc) )
        return pc

    def download(self, files=[], localdestpath='.', compression='gz', bg=False, cb=None):
        """ transfer files from a remote location

            this operation is designed to be threaded

            files = [ [ source_full_path_and_name, dest_relative_path_and_name ],
                   ]

            TODO investigate if files must be provided as pair (to avoid long paths
             and so on...)
        """
        args = (files, localdestpath, compression, cb)
        if bg == False:
            #self._download_tar(files, localdestpath, compression, cb)
            self._download_tar(*args)
        else:
            #self.pending = threading.Thread(target = self._download_tar, args = ( files, localdestpath, compression, cb))
            self.pending = threading.Thread(target = self._download_tar, args = args)
            self.pending.start() 



    def _download_tar(self, source, localdestpath='.', compression='gz', bg=False, cb=None ):
        """ download files using the tar file
            no progress will be available when downloading
            how to handle dirs versus files?

            /garihome/forli/libs/catrame/
        """
        self._status = {'completed' : False, 'error' : None} 
        # XXX TO DO ADD HELPER PRE_FUNCTION TO CREATE BG THREAD...
        if not os.path.isdir(localdestpath):
            self.dprint("ERROR: local destination path is not a dir [%s], returning" % localdestpath)
            self._status['error'] = 'localdestpath is not a dir'
            return
        os.chdir(localdestpath)

        self._problematic = []
        self._status['completed'] = False
        self._counter = 0 # No progress is available
        # test if the remote path exists
        if not self._ready:
            self.dprint("Transfer not ready. Returning...")
            if not cb == None:
                cb("transfer not ready")
            return -1

        # find which compression option is requred
        #if compression == None :
        #    opt = ''
        #    mode = 'r'
        #elif compression == 'gz' :
        #    opt = 'z'
        #    mode = 'r:gz'
        #elif compression == 'bz2': 
        #    opt = 'j'
        #    mode = 'r:bz2'
        #
        #self.dprint('\n\n\n\nTar mode is [%s], opt[%s]' % (mode, opt))
        self._running = True
        #print "RaccoonSshTools.py > _download_tar"
        for fname in source:
            if not self.ssh.exists(fname):
                self._problematic.append([fname, 'not existent file'])
                self.dprint("the file [%s] does not exist, skipping..." % f)
                if not cb == None: cb("non-existent file [%s]" % fname)
                continue            # files must be stored as fullpath?
            #if f[-1] == '/': 
            #    self.dprint("the request was about a dir, probably [%s]" % f)
            #    f = f[:-1] # it's a dir
            #f = f.rsplit('/', 1)
            #if len(f) == 2:
            #    dname = f[0]
            #    fname = f[1]
            #else:
            #    cd = "."
            #    fname = f[0]
            #
            try:
            #if 1:
                if self._STOP:
                    self.dprint("Stop requested, halting")
                    self.close()
                    return
                #cmd = 'cd %s; tar %scf - "%s"' % (dname, opt, fname)
                #self.dprint("executing remote command [%s]" % cmd)
                #self.stdin, self.stdout, self.stderr = self.ssh.execmd(cmd, getlines=False, full=True)
                #print "STDIN ", self.stdin
                #print "STDOUT", self.stdout
                #print "STDERR", self.stderr
                #print "HERE THE ERROR SHOULD SHOW UP"
                #print "OPENSSHFILE", f
                fp, sftp = self.ssh.openfile(fname)
                #print "TARFILE", 
                self.tarfile = tarfile.open(fileobj = fp)
                #print "THERE WERE NO ERRORS?"
                self.tarfile.extractall()
                self._counter += 1
                self.tarfile.close()
                #self.stdin.close()
                #self.stdout.close()
                #self.stderr.close()
                fp.close()
                sftp.close()
            #else:
            except:
                #print "ERROR SOMEWHERE HERE", sys.exc_info()[1]
                if not cb == None: cb("eror: %s" % sys.exc_info()[1])
                self._problematic.append([fname, 'not existent file'])

        self._running = False
        self._status = {'completed' : True, 'error' : None}        
        if not cb == None: cb('completed')





    def progress(self, percent=False):
        """ available only when uploading by counting the
            input files processed
        """
        if percent:
            try:
                return (float(self._counter)/self._total)*100.
            except ZeroDivisionError:
                return 0.0
                
        return self._counter




        



