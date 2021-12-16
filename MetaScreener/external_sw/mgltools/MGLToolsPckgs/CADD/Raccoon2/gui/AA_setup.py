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


import CADD.Raccoon2
# Raccoon stuff
import CADD.Raccoon2.HelperFunctionsN3P as hf
import RaccoonBasics as rb
import RaccoonEvents
import RaccoonServers
import RaccoonServices
from DebugTools import DebugObj # FIXME? fragile? use CADD.Raccoon2.gui.DebugTools?
import os, Pmw
from PmwOptionMenu import OptionMenu as OptionMenuFix
import Tkinter as tk
import tkMessageBox as tmb
import tkFileDialog as tfd
import platform
import paramiko as pmk
from multiprocessing import cpu_count

from PIL import Image, ImageTk
# mgl modules
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction # as cb
# XXX provided by Racc default widget
#from mglutil.util.packageFilePath import getResourceFolderWithVersion



class SetupTab(rb.TabBase, rb.RaccoonDefaultWidget):
    
    def __init__(self, app, parent, debug=False): # Initialize to the default resource
        rb.TabBase.__init__(self, app, parent, debug = False)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.resource = self.app.resource
        self.app.eventManager.registerListener(RaccoonEvents.SetResourceEvent, self.handleResource)
        self.app.eventManager.registerListener(RaccoonEvents.ServerConnection, self.handleConnection)
        self.app.eventManager.registerListener(RaccoonEvents.ServerDisconnection, self.handleDisconnection)
        self.app.eventManager.registerListener(RaccoonEvents.SshServerManagerEvent, self._populateservertoolbar)
        self.initIcons()
        self._makeresourcechoice()

    def handleConnection(self, event=None):
        """ performs all the operations relative to connection to a server"""
        if self.app.server == None:
            #print "handleConnection called with no server [THIS SHUOLDN'T HAPPEN?]"
            return
        # scan the server for services
        self.app.setBusy()
        #print "BHUSY SCANNING"
        self.app.server.scan()
        #print "READYZ AFTER SCANNING"
        self.app.setReady()
        # search for services and libraries
        self._updateserverinfo()
        # update the optionmenu (the connection could come from somewhere else)
        self.serverChooser.setvalue(self.app.server.name())
        self.app.setBusy()
        e = RaccoonEvents.SyncJobHistory()
        self.app.eventManager.dispatchEvent(e)
        self.app.setReady()





    def handleDisconnection(self, event=None):
        """ clean up all the things for disconnection"""
        # reset the server chooser
        null = self.serverChooser_NULL
        self.serverChooser.setvalue(null)
        self.setService(reset=True)
        # clean up the services info
        self._updateserverinfo()

    def _makeresourcechoice(self):
        """ build the widgets for choosing resources"""
        FRAME = tk.Frame(self.parent)
        FRAME.pack(anchor='n', side='top', expand=0, fill='x')
        group = Pmw.Group(FRAME, tag_text = 'Computational resource', tag_font=self.FONTbold)
        frame = tk.Frame(group.interior())
        self._res_var = tk.StringVar()
        self.b1 = tk.Radiobutton(frame, text='   Local\n   workstation', variable=self._res_var, image=self._ICON_workstation,
            compound = 'left', value='local', command=self.setResource_cb, indicatoron=False, **self.BORDER)
        self.b1.configure(width=128, state='disabled')
        self.b1.pack(side='left',anchor='center')

        self.b2 = tk.Radiobutton(frame, text='   Linux\n   cluster', variable=self._res_var, image=self._ICON_cluster,
            compound='left', value='cluster', command=self.setResource_cb, indicatoron=False, **self.BORDER)
        self.b2.configure(width=128)
        self.b2.pack(side='left', anchor='center',padx=1)

        self.b3 = tk.Radiobutton(frame, text='   Opal\n   server', variable=self._res_var, image = self._ICON_opal,
            compound='left', value='opal', command=self.setResource_cb, indicatoron=False, **self.BORDER)
        self.b3.pack(side='left')
        self.b3.configure(width=128, state='disabled')

        frame.pack(side='top', expand=0, anchor='n')
        group.pack(fill='none',expand=0,anchor='center',side='top',padx=5, pady=5, ipadx=5,ipady=5)

    def setResource_cb(self, event=None):
        """event for the choice of resources"""
        resource = self._res_var.get()
        event = RaccoonEvents.SetResourceEvent(resource)
        self.app.eventManager.dispatchEvent(event)
        

    def updateServerList_cb(self, event=None):
        """dispatch the event of updated (added/removed) server
            list 
        """
        event = RaccoonEvents.UpdateServerListEvent()
        self.app.eventManager.dispatchEvent(event)

    def handleResource(self, event):
        self.setResource(event.resource)

    def setResource(self, resource):
        """ """
        if resource == self.resource:
            return
        self.resource = resource
        self.app.resource = self.resource
        
        self.app.parent.title("AutoDock | Raccoon \t[ resource : %s ]" % self.resource)
        if self.resource == 'local':
            self.setLocalResource()
        elif self.resource == 'cluster':
            self.setClusterResource()
        elif self.resource == 'opal':
            self.setOpalResource()

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH

        f = icon_path + os.sep + 'system.png'
        self._ICON_sys = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'floppy.png'
        self._ICON_floppy = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'open.png'
        self._ICON_open = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'autodock.png'
        self._ICON_autodock = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'opal.png'
        self._ICON_opal = ImageTk.PhotoImage(Image.open(f))
        
        f = icon_path + os.sep + 'cluster.png'
        self._ICON_cluster = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'workstation.png'
        self._ICON_workstation = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'raccoon.png'
        self._ICON_raccoon = ImageTk.PhotoImage(Image.open(f))
        
        f = icon_path + os.sep + 'refresh.png'
        self._ICON_refresh = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'disconnect.png'
        self._ICON_disconnect = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'wizard.png'
        self._ICON_wizard = ImageTk.PhotoImage(Image.open(f))




############### Local section


    def setLocalResource(self):
        """master function to be called when resource is set to local"""
        self._makelocalpanel()





    def _makelocalpanel(self):

        """ populate the frame in the setup with the summary of local resources info
        
            NOTE this function should be called when preferences are changed (i.e. default data dir)
        
        """
        #print "setupTab> set resource gui to LOCAL |",
        self.resetFrame()

        # docking engine
        group = Pmw.Group(self.frame, tag_text = ' Docking engine', tag_font=self.FONTbold, tag_image = self._ICON_autodock,
        tag_compound='left')
        g = group.interior()
        f = tk.Frame(g)
        var = tk.StringVar(value='vina')
        tk.Radiobutton(f, text='AutoDock', variable = var,value='autodock').pack(side='left', expand=1,fill='y',anchor='nw')
        tk.Radiobutton(f, text='Vina', variable = var,value='vina').pack(side='left', expand=1,fill='y',anchor='ne')
        f.pack(side='top', anchor='n', expand=0, fill='x')
        
        self._localbinlabel = tk.Label(g, text='/usr/local/bin/autodock4', font=self.FONT)
        self._localbinlabel.pack(side='top', anchor='n', expand=0, fill=None)
        tk.Button(g, text='Set executable...', **self.BORDER).pack(side='top',
            anchor='n', expand=1,fill='x', padx=5, pady=3)

        group.pack(fill='y',expand=0,anchor='n',side='top',padx=5, pady=5, ipadx=5,ipady=5)


        # system info
        group = Pmw.Group(self.frame, tag_text = 'System information', tag_font=self.FONTbold)
        group.pack(expand=1, fill='x',anchor='w', side='top',padx=5, pady=5, ipadx=3, ipady=3)
        g = group.interior()
        f = tk.Frame(g)
        f.pack(expand=1,fill='both')
        self.local_table = hf.SimpleTable(f, title_item='column', 
                title_color ='#d8daf8', cell_color='white', 
                title_font = self.FONTbold, cell_font=self.FONT,
                autowidth=True)
        self._updatelocalinfotable()

        tk.Button(g, image = self._ICON_open, compound='left', text='Set working directory', command=self._setlocalwd,
                **self.BORDER).pack(expand=0,fill='x',anchor='s',padx=3, pady=2)

        self.frame.pack(expand=0, fill='none',anchor='n')


        #print "Raccoon GUI resource:", self.app.resource

    def _setlocalwd(self, event=None):
        """ ask and set the path of the local wd"""
        t = 'Set new working directory'
        dirname = tfd.askdirectory(parent=self.frame, title = t, mustexist=True)
        if dirname:
            self.app.tempdir = dirname
            self._updatelocalinfotable()


    def _updatelocalinfotable(self):
        data = self._getlocalinfo()
        self.local_table.setData(data)
        

    def _getlocalinfo(self):
        """ gather info data used to populate the local panel"""
        cpu = cpu_count()
        info = hf.getOsInfo()
        os_format = '%s %s (%s)'
        if info['system'] == 'Windows':
            os_string = os_format % (info['system'], info['release'], info['architecture'])
                                    
        elif info['system'] == 'Linux':
            os_string = os_format % (info['system'],
                                    info['release'].split('-')[0],
                                    info['architecture'])
        elif info['system'] == 'Darwin':
            os_string = os_format % ('Mac OS',
                                    info['release'],
                                    info['architecture'])

        data = [ [ 'OS type', os_string ],
                 [ 'number of CPU/cores', cpu],
                 [ 'working directory', hf.truncateName(self.app.tempdir,15)],
                 [ 'available space', hf.checkDiskSpace(self.app.tempdir, human=1)], ]
                 #[ 'working directory', hf.truncateName(self.app.getRacPath(),20)],
                 #[ 'available space', hf.checkDiskSpace(self.app.getRacPath(), human=1)], ]

        return data



############## CLUSTER SECTION


    def setClusterResource(self):
        """ master function to be called when resource is set to cluster"""
        #print "setupTab> set resource gui to CLUSTER |",
        self.resetFrame()
        self._makeinfopanel()
        #self._updateserverinfo() XXX this should be called only upon connection...

    def _makeservertoolbar(self, target):
        """ create the widgets to set/configure the server 
        
            (the binds to the servermanager?)
        """

        f = tk.Frame(target)
        # pulldown
        self.serverChooser = OptionMenuFix(f, labelpos='w', menubutton_width=40,
                            label_text = 'Connection  ',
                            label_font = self.FONT,
                            menubutton_font = self.FONT,
                            menu_font = self.FONT,
                            command = self.chooseServer,
                            menubutton_bd = 1, menubutton_highlightbackground = 'black',
                            menubutton_borderwidth=1, menubutton_highlightcolor='black', 
                            menubutton_highlightthickness = 1,
                            menubutton_height=1,
                            )

        self.serverChooser_NULL = '<no servers>'

        #self.app.eventManager.registerListener(RaccoonEvents.UpdateServerListEvent, self._populateservertoolbar)

        self.serverChooser.pack(expand=1, fill='x', anchor='center', side='left')
        # connect
        #b1 = tk.Button(f, text='C/D', command=None)
        #b1.pack(expand=0, anchor='w', side='left')

        b2 = tk.Button(f, image=self._ICON_sys, text='(S)', command=None)
        b2.pack(expand=0, fill='y', anchor='center', side='left', padx=1)
        b2.configure(command=self._openservermanager, **self.BORDER)

        b = tk.Button(f, text='Disconnect', command=self.closeconnection,
                image=self._ICON_disconnect, compound=None, **self.BORDER)
        b.pack(anchor='se', side='right',expand=0,fill='y')

        b = tk.Button(f, text='Refresh', command=self.refresh,
            image=self._ICON_refresh, compound=None, **self.BORDER)
        b.pack(anchor='se', side='right',expand=0,fill='y',padx=1)

        b = tk.Button(f, text='Prepare', command=self.racconizeServer, 
            image=self._ICON_raccoon, compound=None, **self.BORDER)
        b.pack(anchor='se', side='right',expand=0,fill='y')

        f.pack(expand=0, fill='none', anchor='w',side='top', padx=3, pady=3)
        self._populateservertoolbar()

    def refresh(self, event=None):
        """ check for changes on the server by
            triggering a ServerConnection event
        """
        e = RaccoonEvents.ServerConnection()
        self.app.eventManager.dispatchEvent(e)


    def _populateservertoolbar(self, event=None):
        """ add servers to the list of optionmenu"""
        servers = sorted(self.app.getServerByType('ssh').keys())
        if len(servers) == 0:
            self.serverChooser_NULL = '<no servers>'
            servers = [self.serverChooser_NULL]
        else:
            self.serverChooser_NULL = '<choose a server...>'
            servers = [self.serverChooser_NULL]+servers
        self.serverChooser.setitems(servers)
        if not self.app.server == None:
            #self.serverChooser.setvalue()
            name = self.app.server.properties['name']
            self.serverChooser.setvalue(name)
            #print self.app.server
        else:
            self.serverChooser.setvalue(self.serverChooser_NULL)

    


    def _makeinfopanel(self):
        """ create the panels containing all info about
            the server to which we're connected
        """
        ### info panel
        group = Pmw.Group(self.frame, tag_text = 'Server', tag_font=self.FONTbold)
        g = group.interior()
        self._makeservertoolbar(g)

        # left top frame
        f1 = tk.Frame(g)
        table = tk.Frame(f1)
        self.serverInfoTable = hf.SimpleTable(table, title_item= 'column', 
                title_color ='#d8daf8', cell_color='white', title_width=20,
                title_font = self.FONTbold, cell_font=self.FONT,
                autowidth=True)
        fill = [ [ 'Raccoonized', '--'],
                 [ 'OS type', '--'],
                 [ 'hostname', '--'],
                 [ 'scheduler', '--'],
                 [ 'number of nodes', '--'],
                 [ 'architecture', '--'],
                ]

        self.serverInfoTable.setData( fill )
        table.pack(side='top', anchor='n',padx=3,pady=10)

        f3 = tk.Frame(f1)
        # service choice panel
        self._service_choice = tk.StringVar()
        tk.Label(f3, text="Selected docking service :", font=self.FONT).pack(expand=0,anchor='w',side='top')
        self._service_label = tk.Label(f3, textvar = self._service_choice, font=self.FONTbold, 
            anchor='w', bg='white', **self.BORDER)
        self._service_label.pack(expand=1, fill='both', anchor='w', side='left')
        f3.pack(side='top', anchor='n', padx=2,pady=7, expand=1,fill='x')


        f1.pack(side='left', anchor='n', expand=0, fill='none')

        # right top frame
        f2 = tk.Frame(g)
        # services panel
        self.servicesPanel=Pmw.ScrolledFrame(f2, labelpos='nw', label_text='Available services',
            label_font=self.FONTbold,
            horizflex = 'elastic')
        self.servicesPanel.pack(expand=1,fill='both',anchor='n', side='top', padx=3, pady=1)
        self.servicesPanel.component('clipper').configure(bg='white')
        # keep track of packed widgets of services
        self.servicesPanel.widgets = []
        b = tk.Button(f2, text='Service manager...', height=16, font = self.FONT,
                image=self._ICON_wizard, compound='left', command=self.openServiceManager, **self.BORDER)
        b.pack(anchor='n', side='left',expand=1,fill='x',padx=3, pady=2)
        f2.pack(side='left', anchor='n', expand=1, fill='both')

        # bottom frame
        group.pack(expand=1, fill='both',anchor='center', side='top',padx=5, pady=5)


        self.frame.pack(expand=1, fill='both')

        #print "Raccoon GUI resource:", self.app.resource



    def openServiceManager(self, event=None):
        """ invoke the service manager window """
        if self.app.server == None: return
        sm = ServiceManager(self.app, self.frame)
        sm()
        


    def closeconnection(self,event=None):
        """ disconnect from the currently connected 
            server and set several vars to None 
        """
        if self.app.server == None:
            return
        # TAG  this shouldn't happen
        if self.app.server.transfer._running:
            t = 'Pending operations'
            m = ('There are active transfers using the current '
                'connection.\n\nClosing it now will cause data '
                'loss.\n\nContinue?')
            i = 'warning'
            if not tmb.askyesno(parent=self.frame, title=t, message=m, icon=i):
                return
        self.app.disconnectSshServer()
        # e = RaccoonEvents.ServerDisconnection()
        # self.app.eventManager.dispatchEvent(e)


    def _openservermanager(self, event=None):
        """ open the server manager window"""
        SshServerManagerWin( self.app, parent = self.parent)
        

    def chooseServer(self, server=None, event=None):
        """manage the server selection from pulldown"""
        #self.app.debug = True
        self.app.setBusy()
        if server == None:
            server = self.serverChooser.getvalue()
        if server == self.serverChooser_NULL:
            #tmb.showinfo('No server selected','Choose a server from the list or add a server with the setup button...', parent=self.frame)
            self.app.setReady()
            return
        data = self.app.settings['servers']['ssh'][server]
        if not self.app.server == None:
            if self.app.server.properties['name'] == server:
                self.dprint("already connected to the server, returning")
                self.app.setReady()
                return
        # disconnect first?
        #e = RaccoonEvents.ServerDisconnection()
        #self.app.eventManager.dispatchEvent(e)
        #print "CONNECTING USING DATA", data
        self.dprint("FIRST connection attempt")
        #print "\n\n\n\nCALLED CONNECTION 1"
        if not data['load_sys_host_key'] and not data['pkey'] and not data['password']:
            status = (None, 'no password')
        else:
            self.app.setBusy()
            status = self.app.connectSshServer(server, data) #,usekeys=True)
            self.app.setReady()
        if not status == 'connected':
            err, err_o = status
            self.dprint("Error message:[%s] [obj:%s]" % (err, err_o))
            # handle security errors (password, keys, etc...)
            if err_o in [ pmk.BadHostKeyException, pmk.AuthenticationException, pmk.SSHException, 'no password']:
                #if "host key could not be verified" in err:
                    # workaround for keys issues:
                #    self.dprint("Possible hostname mismatch detected.... trying switching keys off.")
                #    #usekeys = False
                self.dprint("asking for password")
                c = 1
                # ask user for password
                while True:
                    if err_o == 'no password':
                        error = None
                    else:
                        error = err, err_o
                    asking = PasswordPromptWin(self.parent, name=server, data=data, error=error, app=self.app, debug=self.debug)
                    passwd = asking.dialog.get()
                    if passwd == '':
                        self.dprint("Empty password, returning")
                        e = RaccoonEvents.ServerDisconnection()
                        self.app.eventManager.dispatchEvent(e)
                        self.app.setReady()
                        return
                    else:
                        self.dprint("connection attempt #%d" % c)
                        data['password'] = passwd
                        data['pkey'] = None
                        data['load_sys_host_key'] = None
                        self.app.setBusy()
                        print "NOW WE SHOULD BE BUSY"
                        status = self.app.connectSshServer(server, data) #,usekeys=True)
                        if not status == 'connected':
                            err, err_o = status
                            t = 'Connection error'
                            m = ('Error using connection "%s": \n\n%s\n\n'
                                    'Try again?' % (server, status[0]) )
                            i = 'warning'
                            if not tmb.askyesno(parent=self.parent, title=t, message=m, icon=i):
                                self.app.server = None
                                self.dprint("user aborted attempt")
                                self.app.setReady()
                                return
                        else:
                            self.dprint("Connection successful (after password)")
                            self.app.setReady()
                            return
                    c+=1
            # handle any other error
            else:
                msg = ('A connection error has been encountered:\n\n'
                       '%s\n\nInspect the connection settings and try '
                       'again.')
                msg = msg % err
                tmb.showwarning(title="Connection error", message=msg)
                self.app.server = None
                self.app.setReady()
                return
            
    def racconizeServer(self,event=None):
        """ prepare ask the RaccoonServer to prepare the cluster 
            with required directories, etc...
        """
        force = False
        if self.app.server == None:
            t = 'No server'
            m = 'Connect to a server first...'
            tmb.showinfo(parent=self.frame, title=t, message=m)
            return
        if self.app.server.properties['ready']:
            t = 'Warning'
            m = ('The server seems to be already prepared'
                 ' and ready to accept commands, therefore '
                 'there is no need to racconize it again.\n\n'
                 'If you continue forcing the preparation, the data '
                 'already stored on the server (i.e. libraries, services, '
                 'calculation results, etc...) will be lost.\n\n'
                 'Are you sure you want to force overwriting all the '
                 'current server settings?')
            i = 'warning'
            if not tmb.askyesno(parent=self.frame, title=t, message=m, icon=i):
                return
            t = 'Overwriting settings'
            m = ('Are you really *sure*?')
            if not tmb.askyesno(parent=self.frame, title=t, message=m, icon=i):
                return
            force = True
        result = self.app.server.racconize(force=force)
        t = 'Server racconization'
        if result:
            m = 'Server prepared successfully!'
            i = 'info'
            e = RaccoonEvents.ServerConnection()
            self.app.eventManager.dispatchEvent(e)
        else:
            m = 'The server preparation was not succesfull.'
            i = 'error'
        tmb.showinfo(parent=self.frame, title=t, message=m, icon=i)

    def _updateserverinfo(self):
        """ update the panels with the info about server"""
        self.dprint("Updating server info panels")
        self._getservermanifesto()
        self._getclustinfo()
        self._getservicesinfo()

    def _getservermanifesto(self):
        """ query the current server for the manifesto"""
        if self.app.server == None:
            manifesto = None
        else:
            manifesto = self.app.server.manifesto(None)
        self._servermanifesto = manifesto
        
    def _getclustinfo(self):
        """query the server and gather basic cluster info"""


        if self.app.server == None:
            data = [ [ 'Raccoonized', '--'],
                     [ 'OS type', '--'],
                     [ 'hostname', '--'],
                     [ 'scheduler', '--'],
                     [ 'number of nodes', '--'],
                     [ 'architecture', '--'],
                    ]
        else:
            i = self._servermanifesto['host_info']
            racconized = self.app.server.checkServerStatus()
            if racconized: 
                r = 'READY'
            else:
                r = 'NOT READY'
            data = [ [ 'Raccoonized', r ],
                     [ 'OS type', i['os'] ],
                     [ 'hostname', i['hostname'] ],
                     [ 'scheduler', i['scheduler'] ],
                     [ 'number of nodes', i['nodes'] ],
                     [ 'architecture', i['architecture'] ], ]
            # check that there's a known scheduler
            self._checkscheduler(i['scheduler'])
        self.serverInfoTable.setData(data)
        

    def _checkscheduler(self, sched):
        """ be sure that the scheduler is known"""
        if not sched =='?':
            return
        t = 'Scheduler problem'
        m = ('There is no known scheduler on the server '
             'therefore it is not possible '
             'to use it as Linux cluster for dockings.\n\n'
             'Contact your server admin '
             'to install one of the supported schedulers.\n'
             '(See the Raccoon user manual for references)')
        i = 'error'
        tmb.showinfo(parent=self.frame, title=t, message=m, icon=i)
        return


    def _getservicesinfo(self):
        """ populate and arrange services info in the panel
        
        
            NOTE: due to the use of a Pmw.ScrolledFrame
                  it is not possible to get rid of the white
                  background
        """
        # clean up previous widgets
        for w in self.servicesPanel.widgets:
            w.pack_forget()
        if self.app.server == None:
            return

        frame = self.servicesPanel.interior()
        self.servicesPanel.interior().configure(bg='white') #**self.BORDER)
        srvc = self._servermanifesto['services']
        # scan items for max widths
        maxw1 = maxw2 = namew = 0
        for t in sorted(srvc.keys()): # scan service types for max lenght
            if t == 'docking':
                for s in srvc[t]:
                    for kw, value in s.items():
                        if kw == 'name':
                            namew = max (len(s[kw]), namew)
                        else:
                            maxw1 = max(len(str(kw)), maxw1)
                            maxw2 = max(len(str(value)), maxw2)
        namew += 3
        maxw1 += 3
        maxw2 += 3
        self.buttons = []
        c = 0
        for t in sorted(srvc.keys()): # service type
            for s in srvc[t]:         # specific service
                kw = ['type  :']
                val = [' docking']
                name = s['name']
                for k in sorted(s.keys()):
                    #print "KAWA [%s]"% k, s[k]
                    if k == 'name':
                        srv_name = " "+s[k]
                        #print "HIT", srv_name
                    else:
                        kw.append(k+"  :")
                        if isinstance(s[k], list):
                            x = ", ".join(s[k])
                        else:
                            x = str(s[k])
                        val.append(" %s" % x)
                kw = "\n".join(kw)
                val = "\n".join(val)
                f = tk.Frame(frame, bg='#dddddd', relief='raised', width = 500, **self.BORDER)
                #srv_name = "  "+ t.upper()
                # service type
                l1 = tk.Radiobutton(f, text=srv_name, variable=self._service_choice, value=name, command=self.setService_cb,
                    font=self.FONTbold, width = namew, justify='center', anchor='w', indicatoron=True, bg='#dddddd')
                l1.pack(expand=0,fill='none', anchor='w',side='left')
                self.buttons.append(l1)
                cb = CallbackFunction(self.click_cb, (c))
                c+=1
                # service kw
                l2 = tk.Label(f, text=kw,anchor='e', justify='right', bg='#dddddd', width=maxw1, font=self.FONTbold)
                l2.pack(expand=0,fill='none', anchor='w',side='left')
                l2.bind('<Button-1>', cb)
                # service values
                col = 'white'
                col = '#eeffee'
                ff = tk.Frame(f, bg=col, relief='sunken', **self.BORDER) # bd=2)
                l3 = tk.Label(ff, text=val,justify='left', bg=col, width=maxw2, anchor='w', font=self.FONT)
                l3.pack(expand=1,fill='x', anchor='w',side='left')
                l3.bind('<Button-1>', cb)

                ff.pack(expand=1,fill='x',side='top', padx=3, pady=3)
                f.pack(expand=1,fill='x',side='top', padx=3, pady=3)
                f.bind('<Button-1>', cb)
                # separator
                #_sep = tk.Frame(frame,height=1,bd=1,relief='sunken',highlightbackground='black',
                #    borderwidth=2,highlightcolor='black',highlightthickness=1)
                #_sep.pack(expand=1,fill='x', anchor='w',side='top')
                self.servicesPanel.widgets.append(f)
                #self.servicesPanel.widgets.append(_sep)


        self.servicesPanel.reposition()

        # XXX disabled 17.3.2013 SF
        #     the user should do a deliberate choice for this
        #     Maybe add option to define preferred service 
        #     on the server?
        #
        # if only one service is present, automatically select it... is that good?
        #if c == 1:
        #    self.buttons[0].invoke()


    def click_cb(self, count, *args):
        """ catches all clicks within the widgets
            and re-direct them to the radiobutton
        """
        self.buttons[count].invoke()
        

    def setService_cb(self, event=None):
        self.setService()

    def setService(self, reset=False):
        """ set the service to be used for docking
            reset=True is used when disconnecting
        """
        if reset: 
            #print "Resetting service"
            self.app.dockingservice = None
            self._service_choice.set('')
        else:
            #print "USING SERVICE", self._service_choice.get()
            self.app.dockingservice = self._service_choice.get()
        e = RaccoonEvents.ServiceSelected()
        self.app.eventManager.dispatchEvent(e)



    def setOpalResource(self):
        #print "setupTab> set resource gui to OPAL |",
        self.resetFrame()
        tk.Label(self.frame, text='opal resources widget 1').pack()
        tk.Label(self.frame, text='opal resources widget 2').pack()
        tk.Label(self.frame, text='opal resources widget 3').pack()
        self.frame.pack(expand=1, fill='both')
        #print "Raccoon GUI resource:", self.app.resource



class PasswordPromptWin(rb.RaccoonDefaultWidget, DebugObj):
    """prompt the password and show some info if necessary..."""
    def __init__(self, parent, name, data, app, error = None, debug = False):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        DebugObj.__init__(self, debug)
        self.name = name
        self.data = data
        self.error = error
        self.app = app
        title = 'Password connection'

        self.dialog = Pmw.PromptDialog(self.parent, title = title, # label_text='password : ',
            entry_show='*', entry_width=40, entry_justify='center', 
            defaultbutton = 0, buttons = ('Connect with password', 'Cancel'),
            command = self.execute)
        bbox = self.dialog.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)



        parent =  self.dialog.component('dialogchildsite')
        self.dialog.component('buttonbox').button(0).configure(font=self.FONT)
        self.dialog.component('buttonbox').button(1).configure(font=self.FONT)
        self.dialog.component('dialogchildsite').pack_forget()
        self.dialog.component('entryfield').pack_forget()

        g = Pmw.Group(parent, tag_text = 'Connection info', tag_font=self.FONTbold)
        info = [[ 'connection', name],
                [ 'address', data['address'] ],
                [ 'username', data['username'] ],
                ]
        if data['load_sys_host_key']:
            auth = 'system host keys'
        elif data['pkey']:
            auth = 'user defined public key'
        elif data['password']:
            auth = 'password'
        else:
            auth = 'none'
        info.append(['authetication saved', auth])

        table = hf.SimpleTable(g.interior(), title_item='column', 
                title_color ='#d8daf8', cell_color='white', 
                title_font = self.FONTbold, cell_font=self.FONT,
                autowidth=True)
        table.setData(info)
        g.pack(side='top', anchor='n', padx=5, pady=5, ipadx=5, ipady=4, fill='x', expand=0)

        if not self.error == None:
            g = Pmw.Group(parent, tag_text = 'Connection error', tag_font=self.FONTbold)
            f = tk.Frame(g.interior(), bg ='white', **self.BORDER)
            tk.Label(f, text = "%s" % self.error[0], anchor='w', bg='white',
                font=self.FONT).pack(anchor='n',side='top',padx=5, pady=5)
            if self.debug:
                tk.Label(f, text = "DEBUG: %s" % self.error[1], anchor='w', bg='white',
                    font=self.FONTbold, fg='red').pack(anchor='n',side='top',padx=1, pady=5)

            f.pack(side='top', anchor='w',expand=1, fill='both', padx=4, pady=4)
            g.pack(side='top', anchor='n', padx=5, pady=5, ipadx=5, ipady=4, fill='x', expand=0)
            
        msg = 'Insert password to connect to %s (%s)' % (name, data['address'])
        tk.Label(parent, text = msg, justify='left', font=self.FONT).pack(anchor='n',side='top', padx=10, pady=5)
        self.dialog.component('dialogchildsite').pack(side='top', anchor='n',expand=1,fill='both')
        self.dialog.component('entryfield').pack(side='top', anchor='n')
        tk.Frame(self.dialog.component('dialogchildsite'), height=10).pack(side='top', anchor='w', expand=1, fill='x',padx=2, pady=2)
        #tk.Frame(self.dialog.component('hull'), height=10).pack(side='top', anchor='w', expand=1, fill='x',padx=2, pady=5)
        self.app.setBusy()
        self.dialog.activate()

    def execute(self, result):
        if result == None or result == 'Cancel':
            self.dialog.setvalue('')
            #return None
        passwd = self.dialog.get()
        self.dialog.deactivate()
        self.app.setReady()
        return passwd
        

class SshServerManagerWin(rb.RaccoonDefaultWidget):
    """ provide interface for adding a new connection to Raccoon"""

    def __init__(self, app, parent=None ):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.app = app
        # defaults and texts
        self._save_pas_var = tk.BooleanVar(value=False) # save password in the database
        self._new_server_txt = ' < new server >'
        self._CLEAN = True
        self.initIcons()
        # starting
        self.makeWin()
        self.setserverlist()

    def destroy(self, event=None):
        """ close the window
        """
        # trigger the event refresh of server list
        if not self._CLEAN:
            t = 'Connection modified'
            i = 'warning'
            m = ('A connection has been modified but not saved.\n'
                 'Are you sure you want to leave?')
            if not tmb.askyesno(parent = self.win.interior(), title=t, message=m, icon=i):
                return
        self.win.deactivate()

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH

        f = icon_path + os.sep + 'floppy.png'
        self._ICON_save = ImageTk.PhotoImage(Image.open(f))        

        f = icon_path + os.sep + 'add.png'
        self._ICON_add = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'remove.png'
        self._ICON_remove = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'openSmall.png'
        self._ICON_open = ImageTk.PhotoImage(Image.open(f))

    def makeWin(self):
        """ visualize the interface"""
        self.win = Pmw.Dialog(self.parent, title='Connection manager', hull_width = 1000, hull_height=1400,
            buttons = ('Close',), command = self.destroy)
        bbox = self.win.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)

        #self.win.component('buttonbox').button(0).configure(font=self.FONT)
        #self.win.component('buttons')['Close']
        self.pane = Pmw.PanedWidget(self.win.interior(), orient='horizontal', handlesize=-1,
            separatorthickness=10, separatorrelief='raised', )

        self.left = self.pane.add('info', min=40)
        self.right =  self.pane.add('viewer', min=130)
        handle = self.pane.component('handle-1')
        sep = self.pane.component('separator-1')

        self.pane.component('handle-1').place_forget()
        self.pane.component('handle-1').forget()
        self.pane.component('handle-1').pack_forget()
        self.pane.component('handle-1').grid_forget()
        self.pane.component('separator-1').configure(bd =2, #bg = '#999999'
            highlightthickness=1, highlightbackground='black', highlightcolor='black')
        # nail handle
        tk.Frame(sep,height=40,width=4,bg='#fffeee',relief='sunken',bd=1,highlightbackground='black',
            highlightthickness=1).pack( anchor='center', padx=2,pady=2,side='left',expand=0,fill=None)

        # LEFT
        g = Pmw.Group(parent = self.left, tag_text = 'Saved connections', tag_font = self.FONTbold)
        g.pack(expand=1, fill='both', padx=3, pady=3)
        self.serverlist = Pmw.ScrolledListBox(parent = g.interior(), selectioncommand=self.selectionCommand,
            listbox_font = self.FONT, usehullsize = 0)
        #self.serverlist.listbox.configure(bg='white')
        self.serverlist.pack(expand=1, fill='both', padx=3, pady=2)

        # button toolbar
        f = tk.Frame(g.interior())
        # new button
        tk.Button(f, text='', image=self._ICON_add, compound='left',font=self.FONT,
                command=self.initNewConnection,height=22, **self.BORDER).pack(anchor='w',
                side='left', padx=0,pady=2,expand=0)
        # del button
        tk.Button(f, text='', image=self._ICON_remove, compound='left',font=self.FONT,
                command=self.delhost,height=22, **self.BORDER).pack(anchor='w',
                side='left', padx=1,pady=2,expand=0)
        f.pack(expand=0,fill='none', anchor='w', side='left', padx=4, pady=3)


        # RIGHT
        bpanel = tk.Frame(self.right)
        f = tk.Frame(bpanel)
        f.pack(expand=0,fill='none', anchor='w', side='left', padx=15) # SPACER FROM HANDLE
        self.info = tk.Frame(self.right, relief='groove', **self.BORDER)

        # server name:
        f = tk.Frame(self.info)
        tk.Label(f, text='server name:', anchor='e', width=14,font=self.FONT).pack(anchor='w', side='left')
        self.info_name = Pmw.EntryField( f, validate = {'min':1,'minstrict':0}, entry_width=30, entry_font = self.FONT)
        self.info_name.pack(anchor='w', side='left', expand=1, fill='x')
        self.info_name.component('entry').bind('<KeyRelease>', self.touched)
        f.pack(side = 'top', expand=0, fill='x', anchor='w',pady=4,padx=3)

        # address
        f = tk.Frame(self.info)
        tk.Label(f, text='address:', anchor='e', width=14, font=self.FONT).pack(anchor='w', side='left')
        self.info_address = Pmw.EntryField( f, validate = {'validator': hf.validateHostname, 'min':1,'minstrict':0},entry_width=30, entry_font = self.FONT)
        self.info_address.pack(anchor='w', side='left', expand=1, fill='x')
        self.info_address.component('entry').bind('<KeyRelease>', self.touched)
        f.pack(side = 'top', expand=0, fill='x', anchor='w',pady=4,padx=3)

        # username
        f = tk.Frame(self.info)
        tk.Label(f, text='username:', anchor='e', width=14, font=self.FONT).pack(anchor='w', side='left')
        self.info_username = Pmw.EntryField( f, validate = {'min':1,'minstrict':0}, entry_width=30, entry_font = self.FONT)
        self.info_username.pack(anchor='w', side='left', expand=1, fill='x')
        self.info_username.component('entry').bind('<KeyRelease>', self.touched)
        f.pack(side = 'top', expand=0, fill='x', anchor='w',pady=4,padx=3)

        # authentication
        self.authMethod = tk.StringVar(value='password')
        f = tk.Frame(self.info)
        tk.Label(f, text='authentication:', anchor='e', width=14, font=self.FONT).pack(anchor='n', side='left')
        g = tk.Frame(f, relief = 'groove', bd = 2) #Pmw.Group(self.info, tag_text = 'Authentication method', tag_font=self.FONT)
        
        x = tk.Frame(g)
        self.authMethod_password = tk.Radiobutton(x, text='password', value='password', 
            variable = self.authMethod, font=self.FONT, command=self.setAuthMethod)
        self.authMethod_password.pack(side='left', anchor='w', padx = 3)

        self.authMethod_file = tk.Radiobutton(x, text='load key file', value='file', 
            variable = self.authMethod, font=self.FONT, command=self.setAuthMethod)
        self.authMethod_file.pack(side='left', anchor='w', padx = 3)

        self.authMethod_system = tk.Radiobutton(x, text='system key file', value='system', 
            variable = self.authMethod, font=self.FONT, command=self.setAuthMethod)
        self.authMethod_system.pack(side='left', anchor='w', padx = 3)
        x.pack(side='top', anchor='w')

        # authentication selection
        self.authPanel = tk.Frame(g)

        ### password selection
        self._passwdFrame = tk.Frame(self.authPanel)
        self.info_password = Pmw.EntryField( self._passwdFrame, entry_show='*', entry_width=30, entry_font = self.FONT)
        self.info_password.pack(side='top', anchor='w', expand=1, fill='x',padx=3, pady=3)
        self.info_password.component('entry').bind('<KeyRelease>', self.touched)
        # password (x) save
        self._save_pas_but = tk.Checkbutton(self._passwdFrame, text='save password', var= self._save_pas_var, onvalue=True,
            font=self.FONT, anchor='w', offvalue=False, command=self.showwarning)
        self._save_pas_but.pack(side='top', anchor='w', expand=1, fill='x',padx=3, pady=3)


        ### custom key file
        self._keyFileFrame = tk.Frame(self.authPanel)
        tk.Button(self._keyFileFrame, image=self._ICON_open, command=self.openKeyFile, 
            **self.BORDER).pack(side='left', anchor='w', padx=3, pady=3)
        self.info_keyfile = tk.Label(self._keyFileFrame, width = 30, font=self.FONT, relief='flat', 
            bg='white', **self.BORDER)
        self.info_keyfile.value = None
        self.info_keyfile.pack(side='left', anchor='w',padx=3, pady=3)
        tk.Label(self._keyFileFrame, text = " ").pack(side='top',anchor='n')


        ### system key file
        self._sysFileFrame = tk.Frame(self.authPanel)
        tk.Label(self._sysFileFrame, text = " ").pack()
        tk.Label(self._sysFileFrame, text = " ").pack()

        self.authPanel.pack(side='left', anchor='w')

        g.pack(side = 'top', expand=0, fill='x', anchor='w', padx=4, pady=3)
        f.pack(side = 'top', expand=0, fill='x', anchor='w') #, padx=4,pady=3)

        #f.grid(row=7, column=1, sticky='w', padx=1, pady=2)


        self.setAuthMethod() # populate the auth widgets
        self._CLEAN = True # restore the clean status after self.setAuthMethod()

        # save button
        tk.Button(self.info, text='Save', image=self._ICON_save, compound='left',font=self.FONT,
                command=self.savehost,height=22, **self.BORDER).pack(side='bottom', anchor='s',expand=0, fill = 'x',padx=5, pady=10)


        bpanel.pack(expand=0, fill='x',anchor='n',side='top')
        self.info.pack(side='top', anchor='n', expand=1, fill ='both', padx=15, pady=10,ipady=6,ipadx=6)
        self.pane.setnaturalsize()
        self.pane.pack(expand=1,fill='both')

        self.setserverlist()
        self.win.activate() #geometry='centerscreenalways')

    def setAuthMethod(self, event=None):
        """ called by radiobuttons for setting authentication method"""
        #print "CALLING SELFTOUCHED"
        self.touched(event)
        method = self.authMethod.get()
        for f in self._passwdFrame, self._keyFileFrame, self._sysFileFrame:
            f.pack_forget()
        if method == 'password':
            self._passwdFrame.pack(pady=3,fill='x',expand=1)
        elif method == 'file':
            self._keyFileFrame.pack(pady=3,fill='x',expand=1)
        elif method == 'system':
            self._sysFileFrame.pack(pady=3,fill='x',expand=1)
        return
            

    def openKeyFile(self, event=None, fname=None):
        """ select the key file to be used for authentication"""
        # XXX get the last user defined file! poat
        # initialdir = 
        initialdir = None
        if not self.info_keyfile.value == None:
            initialdir = os.path.dirname(self.info_keyfile.value)
        if fname == None:
            t = 'Select key file to import'
            fname = tfd.askopenfilename(parent=self.win.interior(), 
                initialdir = initialdir, title = t)
            if not fname:
                return
        self.setKeyFile(fname)

    def setKeyFile(self, fname):
        """ test that the key file is accessible"""
        self.info_keyfile.value = None
        self.info_keyfile.configure(text = '')
        # XXX set variable to null!
        if not os.access(fname, os.R_OK):
            t = 'Key file error'
            i = 'warning'
            m = ('The selected file is not readable.\nSelect another file.')
            tmb.showinfo(parent=self.win.interior(), title=t,
                icon=i, message=m)
            return False
        short = hf.truncateName(fname, 30)
        self.info_keyfile.configure(text = short)
        self.info_keyfile.value = fname
            


    def touched(self, event=None):
        """ triggered every time one of the entries get the 
            focus, to trace user input
        """
        skip = [ 37, 50, 64, 108, 105, 62, 113, 114, 111, 116 ]
        if event:
            if event.keycode in skip:
                return
            #print "keyvcode", event.keycode
        self._CLEAN = False

    def askConfirm(self, event=None):
        """ generic confirmation request when not clean"""
        t = 'Connection modified'
        i = 'info'
        m = ('Changes to current connection have not been saved.\n'
             'Continue?')
        return tmb.askyesno(parent=self.win.interior(), title=t, icon=i, message=m)


    def selectionCommand(self, null=False):
        """ """
        if null or self.serverlist.getvalue()[0] == self._new_server_txt:
            self.initNewConnection()
            return
        if not self._CLEAN:
            if not self.askConfirm():
                return
        item = self.serverlist.getvalue()[0]
        s = self.app.settings['servers']['ssh'][item]
        addr = s['address']
        uname = s['username']
        self.info_name.setvalue(item)
        self.info_address.setvalue(s['address'])
        self.info_username.setvalue(s['username'])
        # check authentication settings
        # check system key
        if s['load_sys_host_key']:
            self.authMethod_system.invoke()
        # check user-set file
        elif not s['pkey'] == None:
            self.authMethod_file.invoke()
            self.setKeyFile(s['pkey'])
        # check password
        elif not s['password'] == None:
            self.authMethod_password.invoke()
            passwd = s['password']
            if not passwd == None:
                #print "ZET PASSWERD"
                self.info_password.setvalue(passwd)
            else:
                #print "NO PAZZERD"
                self.info_password.setvalue('')
            if self.app.getServerByName(item).has_key('_save_passwd_'):
                self._save_pas_var.set(True)
                self._save_pas_but.select()
            else:
                self._save_pas_var.set(False)
                self._save_pas_but.deselect()
        self._CLEAN = True

    def initNewConnection(self, event=None):
        """ clean all the fields for a new connection"""
        if not self._CLEAN:
            if not self.askConfirm():
                return
        for x in [ self.info_name, self.info_address, self.info_username, self.info_password]:
            x.setvalue("")
        self._save_pas_but.deselect()
        self.authMethod_password.invoke()
        self.info_keyfile.value = None
        self.info_keyfile.configure(text = '')
        self._CLEAN = True


    def savehost(self):
        """ save current host in the server db"""
        # check that all entries are validated
        pool =  [ [ self.info_name, 'name' ],
                  [ self.info_address, 'address'],
                  [ self.info_username, 'username'],
                ]
                  #[ self.info_password, 'password'],
                  # XXX add pkey here
                 # ]
        err = []
        server = { 'name': None, 'address': None, 'username' : None, 'load_sys_host_key': False,
                    'password' : None, 'pkey' : None, 
                    }

        # check of text values
        for entry, msg in pool:
            if not entry.checkentry() == Pmw.OK:
                err.append(msg)
            else:
                server[msg] = entry.getvalue()

        # check of validation method
        method = self.authMethod.get()
        #print "ETHODS", method
        if method == 'system':
            server['load_sys_host_key'] = True
        elif method == 'file':
            fname = self.info_keyfile.value
            if not fname:
                err.append('host key file (invalid)')
            else:
                server['pkey'] = self.info_keyfile.value
        elif method == 'password':
            #print "PASSWORD"
            if not self.info_password.checkentry() == Pmw.OK:
                err.append('password')
                #print "ERROR READING PASSWD"
            else:
                #print "FINE READING PASSWD"
                server['password'] = self.info_password.getvalue()
                if self._save_pas_var.get():
                    server['_save_passwd_'] = None
        if len(err):
            msg = 'The following fields are not filled correctly:\n\n'
            msg += "\n".join([" - %s" % x for x in err])
            msg += '\n\nThey must be corrected before the server entry can be saved.'
            tmb.showerror(title='Error',message=msg, parent=self.win.interior())
            return

        # check that the name is not in use
        if self.info_name.getvalue() in self.app.settings['servers']['ssh'].keys():
            msg = ('Update existing server settings? ')
            if not tmb.askyesno(title='Warning',message=msg, parent=self.win.interior(), icon='info'):
                return

        # check passwdd policy
        # save the data
        name = server.pop('name')
        self.app._LAST = server
        # print "GOUNG TO SAVE THIS", server
        self.app.addServer(_type='ssh', name=name, info=server)
        #self.app.settings['servers']['ssh'][name] = server
        #self.app.saveServerInfo()
        # self.app.readServerInfo() ??? XXX required?

        # refresh list of srervers in the widget
        self.setserverlist()
        self._CLEAN = True
        # trigger event for server updates
        e = RaccoonEvents.SshServerManagerEvent()
        self.app.eventManager.dispatchEvent(e)

    def delhost(self):
        """ delete saved hosts from the widget and the server database"""
        # FIXME check if the server to be deleted is the current connection?
        try:
            server = self.serverlist.getvalue()[0]
            if server == self._new_server_txt:
                return
        except:
            return
        msg = 'Deleting host:\n\n%s\n\nAre you sure?' % server
        if not tmb.askyesno(title='Warning', message=msg, parent=self.win.interior()):
            return
        #del self.app.settings['servers']['ssh'][server]
        self.app.delServer(_type='ssh', name=server)
        self.setserverlist()
        self.selectionCommand(null=True)
        # trigger event for server updates
        e = RaccoonEvents.SshServerManagerEvent()
        self.app.eventManager.dispatchEvent(e)



    def showwarning(self, event=None):
        """ show password warning"""
        self.touched()
        if not self._save_pas_var.get():
            return
        msg = ( "The password will be saved with no encryption "
                "in the local Raccoon settings file.\n\nAre you sure you "
                "want to save it?"
                )
        if not tmb.askyesno(title='WARNING!', message=msg, parent=self.win.interior(), icon='warning'):
            self._save_pas_but.deselect()
        else:
            self._save_pas_but.select()


    def setserverlist(self, event=None):
        """ update the widget containing the list of saved servers"""
        serv_name_list = sorted( self.app.settings['servers']['ssh'].keys() )
        #serv_name_list.append(self._new_server_txt)
        self.serverlist.setlist(serv_name_list)


class ServiceManager(rb.PanedManager):
    """ provide gui for adding/removing services

        EVENTS!
        - new service
        - refresh new services
    """

    def __init__(self, app, parent=None, wtitle='Service manager', ltitle='Installed', rtitle='Settings' ):
        rb.PanedManager.__init__(self, app, parent, wtitle, ltitle, rtitle)
    
        # recognized services
        self._tags = { 'docking' : '[DOCKING]: ',
                     #'library_host': '[LIB_HOST]',
                     #'library_upload': '[LIB_UPLOAD]',
                   }
        self.initIcons()
        self.listcontainer.default = '< new >'
        self.listcontainer.configure(selectioncommand=self.choice)
        self.service_template = None
        self.frame = tk.Frame(self.right)
        self.createToolbar()
        self.createPanels()
        m = 'Select an existing service or create a new one'
        tk.Label(self.frame, text=m, font=self.FONT).pack(anchor='center',expand=1,fill='both')
        self.frame.pack(expand=1, fill='both')

        self.win.configure(command=self.destroy)
        self.win.deactivate() # ???
        #self.win.activate() # ???


    def destroy(self, event=None):
        """ close the window
        """
        # trigger the event refresh of server list
        if not self.service_template == None:
           if not self.service_template._CLEAN:
                t = 'Service modified'
                i = 'warning'
                m = ('A service has been modified but not saved.\n'
                     'Are you sure you want to leave?')
                if not tmb.askyesno(parent = self.win.interior(), title=t, message=m, icon=i):
                    return
        self.win.deactivate()


    def createToolbar(self):
        """ create the left panel toolbar (+/-) """
        f = tk.Frame(self.left)
        # add
        self._add = tk.Button(f, text='', image=self._ICON_add, compound='left',font=self.FONT, # NEW
                command=self.newTemplate,height=22, **self.BORDER)
        self._add.pack(anchor='w', side='left', padx=0,pady=2,expand=0)

        # delete
        tk.Button(f, text='', image=self._ICON_remove, compound='left',font=self.FONT, # DEL
                command=self.delete,height=22, **self.BORDER).pack(anchor='w',
                side='left', padx=1,pady=2,expand=0)

        f.pack(expand=0,fill='none', anchor='w', side='left', padx=1) # SPACER

        tk.Button(self.right, text='Save', image=self._ICON_save, compound='left', font=self.FONT,
        command=self.install,height=22, **self.BORDER).pack(anchor='s',
        side='bottom', padx=0,pady=2,expand=1, fill='x')

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'floppy.png'
        self._ICON_save = ImageTk.PhotoImage(Image.open(f))        

        f = icon_path + os.sep + 'add.png'
        self._ICON_add = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'remove.png'
        self._ICON_remove = ImageTk.PhotoImage(Image.open(f))


    def install(self, event=None):
        """ starter for the service template callback"""
        if self.service_template == None:
            return
        self.service_template.install()
        self._getcurrentservices()
        self.service_template._CLEAN = True
        self.app.setBusy()
        e = RaccoonEvents.ServerConnection()
        self.app.eventManager.dispatchEvent(e)
        self.app.setReady()

        
                
    def delete(self):
        """ delete the service from the server"""
        # XXX FIXME manage when the currently selected service is deleted!
        name = self.listcontainer.getcurselection()
        if len(name) == 0:
            return
        name = name[0]
        name = name.split(']: ',1)[1]
        #print "DELETING NAME", name
        if name == self.listcontainer.default:
            return

        t = 'Remove service'
        m = ('The service "%s" is going to be removed from the server.\n\n'
             'Are you sure?' ) % name
        i = 'warning'
        if not tmb.askyesno(parent=self.frame, title=t, message=m, icon=i):
            return
        self.app.server.delService(name)
        self._getcurrentservices()

        #print "\n" * 10, "SELECT NULL!"
        # select the null
        #self.listcontainer.component('listbox').selection_set('end')
        #self.listcontainer.setvalue(self.listcontainer.default)
        self.newTemplate()
        #self.choice(forcenull=True)

        # trigger the update of the services
        e = RaccoonEvents.ServerConnection()
        self.app.eventManager.dispatchEvent(e)


    def newTemplate(self, event=None):
        """ clean up the entry"""
        if not self.service_template == None:
            if not self.service_template._CLEAN:
                t = 'Service modified'
                i = 'warning'
                m = ('Unsaved changes will be lost.\n'
                     'Continue?')
                if not tmb.askyesno(parent = self.win.interior(), title=t, message=m, icon=i):
                    return
        try:
            self.frame.pack_forget()
        except:
            # first time...
            pass

        self.frame = tk.Frame(self.right)
        self.service_template = VinaDockingTemplate(app=self.app, parent=self.frame, data=None)
        self.frame.pack(expand=1, fill='both', anchor='w', side='top')


    def _getcurrentservices(self):
        """ retrieve info about known and currently 
            installed services and update the list 
            container with all services
        """
        # XXX this function for now handles only vina-docking
        # services
        if self.app.server == None:
            return
        self._services = []
        for s in self.app.server.services():
            s_type = s.config['service'] # or s._srvtype
            if s_type in self._tags and s.config['engine'] == 'vina':
                s_name = '%s%s' % (self._tags[s_type], s.config['name'])
                self._services.append(s_name)
        self._services = sorted(self._services) #  + [self.listcontainer.default]
        self.listcontainer.setlist(self._services)
        self.listcontainer.component('listbox').selection_set('end')

    def choice(self, forcenull=False):
        """ listbox choice callback"""
        choice = self.listcontainer.getcurselection()
        if len(choice) == 0:
            return
        choice = choice[0]
        if choice == self.listcontainer.default or forcenull:
            data = None
        else:
            for k, i in self._tags.items():
                if choice.startswith(i):
                    name = choice.split(i,1)[1]
                    #print "SERVICE NAME [%s]" % name

                    srvc = self.app.server.services(name=name)[0]
                    data = srvc.config
                    break
        try:
            self.frame.pack_forget()
        except:
            # first time...
            pass
        self.frame = tk.Frame(self.right)
        self.service_template = VinaDockingTemplate(app=self.app, parent=self.frame, data=data)
        self.frame.pack(expand=1, fill='both', anchor='w', side='top')

         
    

    def createPanels(self):
        """ """
        self._getcurrentservices()

###
###    def populateInterface(self, data):
###        
###        # XXX creation of new service
###        #srv = RaccoonServices.knownservices[stype](server=self, config = service_dict, debug=self.debug )
###        VinaDockingTemplate(app=self.app, parent=self.parent)
###        pass





class VinaDockingTemplate(rb.RaccoonDefaultWidget):
    """ """
    
    def __init__(self, app, parent, data=None):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.initIcons()
        self.app = app
        self.frame = tk.Frame(parent)
        self.engine = 'vina'
        self._CLEAN = True
        self._config = '' # config seed filename

        #if engine == 'vina':
        #    self.setVina()
        #elif engine == 'autodock':
        #    self.setAD()
        #else:
        #    print "UNKNOWN ENGINE!", engine

        #        self.config.update({ 'engine' : None, 'command' : None, 'ver' : None, 
        #                    'multithread' : 1} )
        #        self.config = { 'file' : None, 'name' : '', 'comment': '',
        #            'service' : None, 'validated' : False}
        self.frame.pack(expand=1,fill='both')

        self.service = RaccoonServices.DockingService(server = self.app.server)
        self.service.config['engine'] = self.engine
        self.data = data
        """
        if not data == None:
            print "\n\n====================================="
            for k in self.data:
                print k, self.data[k]
            print "=====================================\n\n"
        """
        self.buildPanel()

    def initIcons(self):
        """ """
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))
        f = icon_path + os.sep + 'installer.png'
        self._ICON_installer = ImageTk.PhotoImage(Image.open(f))        
        f = icon_path + os.sep + 'search.png'
        self._ICON_search = ImageTk.PhotoImage(Image.open(f))        


    def buildconfname(self, event=None):
        """ ButtonRelease -> create config name """
        chars = hf._allowedfilenamechars()
        text = self._name.getvalue()
        if not len(text):
            self._config = ''

        valid = [ x for x in text if x in hf._allowedfilenamechars()]
        valid = "".join(valid).lower() 
        self._config = valid

    def installBinary(self, event=None):
        """ call the service and install the binary"""
        t = 'Install Vina'
        force = False
        if self.service.checkEngine():
            m = ('The program seems to be already '
                 'installed on the server.\n\n'
                 'Overwrite?')
            i = 'warning'

            if not tmb.askyesno(parent=self.frame, title=t, message=m, icon=i):
                return False
            else: force = True
        else:
            m = ('Vina has not been found on the server\n\n'
                 'Do you want to download it and install it now?'
                 )
            i = 'info'
            if not tmb.askyesno(parent=self.frame, title=t, message=m,icon='info'):
                return False

        info = self.service.data_source[self.engine]
        url = info['url']
        ver = info['ver']
        m = ('Use the default AutoDock Vina link? (ver.%s)\n\n(%s)') % (ver, url)
        # ask for another URL or the default
        if not tmb.askyesno(parent=self.frame, title=t, message=m, icon='info'):
            m = ('Insert URL of the Vina installer for Linux:')
            new_url = LinkPrompt(parent=self.frame, title=t, message=m)
            if new_url == False:
                #print "new link aborted..."
                return
            else:
                #print "INSTALLING [%s]" % new_url
                url = new_url
        # start installation 
        status = self.service.installEngine(url = url, force=force)
        
        if status['success']:
            m = 'Installation successful.'
            i = 'info'
            tmb.showinfo(parent = self.frame, 
                title=t, message=m, icon=i)
            bin_name = status['reason'][0]
            #print "XXBIN", bin_name
            self._binary.setvalue(bin_name)
            #e = RaccoonEvents.ServerFeaturesRefresh()
            e = RaccoonEvents.ServerConnection()
            self.app.eventManager.dispatchEvent(e)
            return True
        else:
            err = status['reason']
            m = ('An error has been encountered during '
                 'the installation:\n\n%s' % err)
            i = 'error'
            tmb.showerror(parent=self.frame, title=t, message=m)
            return False 



    def install(self, event=None):
        """ install the service on the server"""
        t = 'Install service'
        for v in self._name, self._binary,  self._multithread:
            if not v.valid():
                m = 'One or more required values are not correct'
                tmb.showerror(parent=self.frame, title=t, message=m)
                return False
        #if not self._config.valid():
        self.buildconfname()


        config = {  'engine' : 'vina',
                    'service': 'docking',
                    'name': self._name.getvalue().strip(),
                    'command' : self._binary.getvalue(),
                    'comment' : self._comment.get('1.0', 'end').strip(),
                    'multithread': self._multithread.getvalue()
                }
        config['comment'] = config['comment'].replace('\n', ' ') # remove spaces!
        # check if service with same name is found
        found_service = self.app.server.services( name = config['name'])
        if len(found_service):
            m = 'Overwrite existing service?\n\n"%s"' % config['name']
            i = 'warning'
            if not tmb.askyesno(parent=self.frame, title=t,message=m,icon=i):
                return False
            # exploit the current info (remove dirname and extension)...
            found_service = found_service[0]
            curr_conf_file = found_service.config['file'].rsplit('/',1)[1]
            curr_conf_file = curr_conf_file.rsplit('.conf',1)[0]
            #self._config.setentry(curr_conf_file)

        config_fname = self._config  + '.conf'
             
        # save config file
        if self.service.initService(config):
            status = self.service.writeServiceConfig(config_fname, force=True)
            value = status['success']
            if not status['success']:
            #    m = 'Service installed successfully'
            #    i = 'info'
            #    value = True
            #else:
                e = status['reason']
                m = ('An error occurred when '
                     'installing the service:\n\n%s' % e)
                i = 'error'
                value = False
        else:
            m = 'The configuration is not valid!'
            i = 'error'
            value = False
        
        if value:
            # register service from config file
            status = self.app.server.addServiceFromConf(config_fname)
            if status['accepted']:
                m = 'Service installed successfully'
                i = 'info'
                value = True
                self._CLEAN = True
            else:
                m = ('A duplicate service has been found!\n'
                     '%s' % status['duplicate'])
                i = 'error'
                value = False
        tmb.showinfo(parent=self.frame, title=t, message=m, icon=i)
        # EVENT ServicesUpdate
        # FIXME add event triggered here...
        return value



    def getValues(self, event=None):
        """return the config dictionary corresponding to widgets"""
        config = {}
        for w in self._widgets.keys():
            if w == 'comment':
                config[w] = self._widgets[k].get('1.0', 'end').strip()
            else:
                config[w] = self._widgets[k].getvalue()
        return config

    def setValues(self, config={}):
        for c in config:
            if c in self._widgets.keys():
                if c == 'comment':
                    try:
                        self._widgets[c].delete('0', 'end')
                    except:
                        #print "CATCHED POSSIBLE EMPTY ERROR!"
                        pass

                    self._widgets[c].insert('end', config[c])
                else:
                    if c == 'file':  
                        value = config[c].rsplit('/',1)[1]
                        value = value.rsplit('.', 1)[0]
                    else:
                        value = config[c]
                    self._widgets[c].setvalue(value)

    def getbinary(self, event=None):
        """ find the binary automatically with the service tools
            by looking for the generic name 'vina' binary
        """
        self.touched()
        self.service.config['command'] = 'vina'
        # strict: don't bother checking if the service has been validated already
        self.app.setBusy()
        binary = self.service.testCommand(strict=False)
        self.app.setReady()
        if binary == False or binary == None:
            t = 'Missing binary'
            m = ('The binary has not been found in the'
                ' specified location.\n\nDo you want to '
                'install it now?')

            if not tmb.askyesno(parent=self.frame, title=t, message=m):
                return
            self.installBinary()
        else:
            self._widgets['command'].setvalue(binary)

    def viewsource(self,event=None):
        """
        """
        #print "\n\n\n", self.service.makeConfig()


    def touched(self, event=None):
        """ triggered every time one of the entries get the 
            focus, to trace user input
        """
        self._CLEAN = False

    def buildPanel(self):
        """
        """
        self._widgets = {}
        # TOOLBAR


        # ENTRIES

        lwidth = 18
        # name
        f = tk.Frame(self.frame) 
        tk.Label(f, text='Name', font=self.FONT,width=lwidth, anchor='e').pack(side='left', anchor='w', padx=5, pady=0)
        self._name = Pmw.EntryField( f, entry_font=self.FONT,
                    validate = {'min':1,'minstrict':0}) 
        self._name.component('entry').bind('<KeyRelease>', self.touched, '+')
        self._name.pack(expand=1, fill='x', side='left', anchor='w')
        self._widgets['name'] = self._name
        f.pack(expand=0, fill='x', side='top',anchor='w', pady=2, padx=10)

        # binary
        f = tk.Frame(self.frame)
        tk.Label(f, text='Executable', font=self.FONT,width=lwidth, anchor='e').pack(side='left', anchor='n', padx=5, pady=7)
        x = tk.Frame(f)
        y = tk.Frame(x)
        self._binary = Pmw.EntryField( y, entry_font=self.FONT,
                    validate = {'min':1,'minstrict':0})
        self._binary.setentry('vina')
        self._binary.pack(expand=1, fill='x', side='left', anchor='w', padx=2)
        self._binary.component('entry').bind('<KeyRelease>', self.touched)
        tk.Button(y, text='bin', image = self._ICON_search, command=self.getbinary,
            **self.BORDER).pack(expand=0, fill='none', side='left', anchor='e', padx=2)
        y.pack(expand=1, fill='x',padx=0,pady=0, side='top', anchor='w')

        # binary installer
        tk.Button(x, text='Install AutoDock Vina on the server...', image=self._ICON_installer, compound='left', 
                font=self.FONT, command=self.installBinary, **self.BORDER).pack(anchor='w',
                side='left', padx=2,pady=2, expand=1,fill='x')
        x.pack(expand=1, fill='x',padx=0,pady=3, side='top', anchor='w')
        self._widgets['command'] = self._binary
        f.pack(expand=0, fill='x', anchor='w', side='top',pady=2, padx=10)

        # multithread
        f = tk.Frame(self.frame) 
        tk.Label(f, text='Multi-thread', font=self.FONT,width=lwidth, anchor='e').pack(side='left', anchor='n', padx=5, pady=4)
        self._multithread = Pmw.Counter( f, autorepeat=False,
            entry_width=5, entryfield_validate = {'validator' : hf.validatePosNonNullInt, 'min':1,'minstrict':0},
            entryfield_value = 1, datatype={'counter': 'integer'})
        # "efficiency at is best" (C) TkInter
        self._multithread.component('entryfield').component('entry').configure(font=self.FONT)
        self._multithread.pack(expand=1, fill='none', side='left', anchor='w')
        self._multithread.component('entryfield').component('entry').bind('<KeyRelease>', self.touched)
        self._multithread.component('entryfield').bind('<KeyRelease>', self.touched)
        self._multithread.component('downarrow').bind('<ButtonRelease-1>', self.touched, '+')
        self._multithread.component('uparrow').bind('<ButtonRelease-1>', self.touched, '+')

        self._widgets['multithread'] = self._multithread
        f.pack(expand=0, fill='x', anchor='w', side='top',pady=2, padx=10)

        #x.pack(expand=1, fill='x', side='top', anchor='w')
        # comments
        f = tk.Frame(self.frame)
        tk.Label(f, text='Comments ', anchor='e', width=lwidth, font=self.FONT).pack(expand=0,
            fill='none', side='left',anchor='n', padx=5, pady=2)
        self._comment = hf.TextCopyPaste( f, bg='white', height=10, width=10, font=self.FONT)
        self._comment.pack(expand=1, fill='both', side='left', anchor='w')
        self._comment.bind('<KeyRelease>', self.touched)
        self._widgets['comment'] = self._comment
        f.pack(expand=1, fill='both', anchor='w', side='top',pady=2, padx=10)

        #f.pack(expand=0, fill='none', anchor='n', side='left',pady=7, padx=10)


        if not self.data == None:
            self.setValues(self.data)


    def populatePanel(self):
        """ populate items with the data
            from the currently installed service
        """

        config = {  'name': self._name.getvalue(),
                    'command' : self._binary.getvalue(),
                    'comment' : self._comment.get('1.0', 'end').strip(),
                    'multithread': self._multithread.getvalue()
                }

        
        


class LinkPrompt:
    """ provide a simple dialog for entering a web url and
        validating it
    """

    def __init__(self, parent, title='', message='' ):
        self.parent = parent
        self.dialog = Pmw.PromptDialog(parent,
            title = title,
            label_text = message,
            entryfield_labelpos='n',
            defaultbutton=0,
            buttons=('OK', 'Cancel'),
            entryfield_validate = {'validator': hf.validateWebLink, 'min':1,'minstrict':0},
            command = self.execute)
        bbox = self.dialog.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)
        self.dialog.activate()

    def execute(self, result):
        if result is None or result == 'Cancel':
            self.dialog.deactivate()        
            return False
        else:
            #result = self.confirm.activate()
            if self.dialog.component('entryfield').valid():
                self.dialog.deactivate()        
                return self.dialog.get()
            else:
                t = 'Invalid web URL'
                m = 'Check the URL inserted and try again\n\n(or press Cancel)'
                i = 'warning'
                tmb.showinfo(parent = self.dialog, title=t, message=m, icon=i)



    
