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

class RaccoonRemoteServerManager(DebugObj):
    """
        Manager for RaccoonSshClient objects.
        The structure of a server is a dictionary item
        containing the following information:

        servers = { 'name' : { 'address': 'xxx',  
                               'user' : 'xxx',    
                               'password': 'xxx',
                               'type'    : 'docking'  # 'md', 'filtering', 'mdprocessing'
                               'type'    : 'ssh'  # 'pbs', 'sge', 'condor'
                               'pubkey_file'  : None,
                              }
    """

    def __init__(self, servers={}, masterpasswd=None):

        self.servers = []

        # masterpasswd should be used to decript 
        # the master password database 
        # (not available in python)
        self.masterpasswd = masterpasswd
        if servers:
            self.initServerDict(servers)
        
    def initServerDict(self, servers={}): 
        """RaccoonSshClient
        initialize the self.servers list
        """
        for s in servers.keys():
            self.addServer(s, servers[s])

    def addServer(self, name, serverinfo = {}, overwrite=False):
        """
        add a new server 'name' to the server dictionary

        the structure of a serverinfo dictionary is :

            server_info = { 'address'   : xxx,
                            'user'      : xxx,
                            'password'  : xxx,
                            'type'    : 'ssh'  # 'pbs', 'sge', 'condor'
                            'pubkey_file'  : None,
                          }
        """
        if name in self.servers.keys() and not overwrite:
            self.dprint('name already in server dbase: change name or check server info.')
            return False
        self.servers[name] = serverinfo
        if not self.servers[name].haskey('ssh'):
            self.servers[s]['ssh'] = RaccoonSshClient( name = s, address = serverinfo['address'],
                  username=serverinfo['user'], password=serverinfo['password'],
                  pkey=serverinfo['pubkey_file'] )
        return True

    def delServer(self, name):
        """ remove a server from the server list 
            if a connection is open, it gets closed first
        """
        self.server[name]['ssh'].closeconnection()
        del self.server[name]

    
    def saveServers(self, fname):
        for s in self.servers.keys():
            data = self.servers[s]
            # encrypt the data HOW? NOT POSSIBLE!

            # json save it.

            # ...

            # profit!
        pass

    def loadServers(self, fname):
        # from file... unencrypted
        pass



