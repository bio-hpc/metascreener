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
import RaccoonLibraries
#import RaccoonServers

import os, Pmw, glob, time, fnmatch
from PmwOptionMenu import OptionMenu as OptionMenuFix
import Tkinter as tk
import TkTreectrl
import tkMessageBox as tmb
import tkFileDialog as tfd


from PIL import Image, ImageTk
import sys, time

# mgl modules
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction #as cb



class LigandTab(rb.TabBase, rb.RaccoonDefaultWidget):
    
    def __init__(self, app, parent, debug=False):
        rb.TabBase.__init__(self, app, parent, debug = False)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.resource = self.app.resource
        self.initIcons()
        self.app.eventManager.registerListener(RaccoonEvents.SetResourceEvent, self.handleResource)
        self.app.eventManager.registerListener(RaccoonEvents.ServerConnection, self.handleServerConnection)
        self.app.eventManager.registerListener(RaccoonEvents.ServerDisconnection, self.handleServerDisconnection)

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'library_small.png'
        self._ICON_lib_small = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'library_small_rem.png'
        self._ICON_lib_small_rem = ImageTk.PhotoImage(Image.open(f))
        
        f = icon_path + os.sep + 'package.png'
        self._ICON_package = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'add.png'
        self._ICON_add = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'remove.png'
        self._ICON_remove = ImageTk.PhotoImage(Image.open(f))


    def handleResource(self, event=None):
        self.setResource(event.resource)


    def handleServerDisconnection(self, event=None):
        """ check for transfers?"""
        #print "GOT TO SERVER DISCONNECTION -->",
        self.handleServerConnection()

    def handleServerConnection(self, event=None):
        """ """
        #print "GOT TO SERVER CONNECTION (LIGAND)"
        self._populateliglibrarytoolbar()

    def setResource(self, resource):
        '''adapt the job manager panel to reflect currently selected resource'''
        if resource == self.resource:
            return
        self.resource = resource
        if resource == 'local':
            self.setLocalResource()
        elif resource == 'cluster':
            self.setClusterResource()
        elif resource == 'opal':
            self.setOpalResource()


    def setLocalResource(self):
        self._makelocliglibrary()
        pass

    def setClusterResource(self):
        #self.frame = tk.Frame(self.parent)
        self._makeclustliglibrary()

        self.frame.pack(expand=1, fill='both', anchor='n', side='top')
        #print "Raccoon GUI lig manager is now on :", self.app.resource

    def setOpalResource(self):
        self.resetFrame()
        pass


    def _makeclustliglibrary(self):
        """ """
        self.resetFrame()
        f = self.frame

        ### LOCAL library panel XXX
        #group = Pmw.Group(f, tag_text = 'Local libraries', tag_font = self.FONTbold)
        #tk.Label(group.interior(), text='NOTHING YET', bg='white').pack(expand=0, fill='x',padx=3)
        #group.pack(expand=0, fill='x',anchor='w', side='top',padx=5, pady=3)

        group = Pmw.Group(f, tag_text = 'Remote libraries', tag_font = self.FONTbold)
        group.pack(expand=1, fill='both',anchor='w', side='top',padx=5, pady=3)
        g = group.interior()

        tbar = tk.Frame(g)
        b1 = tk.Button(tbar, text = 'New', image=self._ICON_add, command = self._call_lib_manager,
            compound='left', font=self.FONTbold, **self.BORDER)
        b1.pack(anchor='w', side='left',padx=1)

        b2 = tk.Button(tbar, text = 'Remove', image=self._ICON_remove, command = self._call_lib_manager_del,
            compound='left', font=self.FONTbold, **self.BORDER)
        b2.pack(anchor='w', side='left',padx=0)

        # check for services upload/download
        # then disable the buttons
        tbar.pack(side='top', anchor='w',padx=2, pady=0)


        #g.pack(expand=1,fill='both',anchor='n', side='top')
       
        f = tk.Frame(g)

        tk.Label(f, text="Selected library :", font=self.FONT).pack(expand=0,anchor='w',side='left', padx=3,pady=1)
        self._selectedLib = tk.Label(f, text = '(none)', bg='white', anchor='w', font=self.FONTbold, **self.BORDER)
        self._selectedLib.pack(anchor='w',side = 'top', expand=1, fill='x', padx=3,pady=1)

        f.pack(expand=0,fill='both',anchor='n', side='top', padx=5, pady =3)



        self.ligLibPanel = TkTreectrl.ScrolledMultiListbox(g, bd=2)
        self.ligLibPanel.listbox.config(bg='white', fg='black', font=self.FONT,
                   columns = ('name', 'items', 'updated', 'format', 
                              'heavy min.', 'heavy max.', 'hba min.', 'hba max.',
                              'hbd min.', 'hbd max', 'mw min', 'mw max', 
                                'tors min', 'tors max', 'atypes') )
        self.ligLibPanel.pack(expand=1, fill='both')
        #self.ligLibPanel.listbox.bind('<ButtonRelease-1>', self._lib_callback)
        self.ligLibPanel.listbox.bind('<Button-3>', self.libselect) #_cb_ssh)
        
        if not self.app.server == None:
            self.dprint("UPDATE THE LIST OF LIBRARIES")


    def libselect(self, event=None):
        """ receive the event of a library selection and
            re-direct it to the resource-specific callback
        """
        self.ligLibPanel.listbox.event_generate('<Button-1>', x=event.x, y=event.y)
        if self.app.resource == 'local':
            self.libselect_cb_local() #event=event)
        elif self.app.resource =='cluster':
            self.libselect_cb_ssh() #event=event)
        elif self.app.resource == 'opal':
            self.libselect_cb_opal() #event=event)
        
    def libselect_cb_local(self): #, event=None):
        """ manage the selection of a library 
            for local submission
        """
        pass
        
    def libselect_cb_ssh(self, libname = None, filters = {}): #, event=None):
        """ manage the selection of a library for cluster submission
            TODO filters now are empty, so the entire library 
                is selected by default
        """
        if libname == None:
            try:
                s = self.ligLibPanel.listbox.curselection()[0]
                sel = self.ligLibPanel.listbox.get(s)[0]
            except:
                return
            libname = sel[0]
        #print "SELECTED LIB=[%s]" % libname
        self.dprint("SELECTED LIB=[%s]" % libname)
        # need ask the server for the lib
        lib = self.app.server.getLibrary(libname)
        if lib == None:
            t = 'Library selection'
            i = 'error'
            m = ('There was an error selecting the library.\n\n'
                 'The library "%s" does not exist on the server' % libname)
            tmb.showinfo(parent=self.ligLibPanel, title=t,message=m, icon=i)
            return False
        self.app.ligand_source = [ {'lib': lib, 'filters' : filters } ]
        self._selectedLib.config(text='%s' % libname)
        e = RaccoonEvents.UserInputRequirementUpdate('lig')
        self.app.eventManager.dispatchEvent(e)
        return True

        
    def libselect_cb_opal(self): #, event=None):
        """ manage the selection of a library for local submission
        """
        pass


    def libdeselect_cb(self):
        """ deselect the library"""
        self.app.ligand_source = []
        self._selectedLib.config(text='%s' % '(none)')
        e = RaccoonEvents.UserInputRequirementUpdate('lig')
        self.app.eventManager.dispatchEvent(e)


    def getSelectedLib(self):
        """ return the library selected for the docking"""
        sel = self.ligLibPanel.getselection

        return 

    def _call_lib_manager(self, event=None):
        """ """
        # test if there's a server
        if self.app.server == None:
            title ='No server selected'
            msg = ('Connect to a server in the Setup tab '
                   'to upload new libraries...')
            tmb.showinfo(parent = self.frame, title = title, message = msg)
            return
        # test if it is racconized
        if not self.app.server.properties['ready']:
            title ='Server is not ready'
            msg = ('The server has not been prepared ("racconized") yet.\n\n'
                   'Prepare it in the Setup tab and try again.')
            tmb.showinfo(parent = self.frame, title = title, message = msg)
            return
        # test if there is an upload service
        # XXX TODO XXX
        LibraryManagerWin(self.app, self.frame)

    def _call_lib_manager_del(self,event=None):
        # test if there's a server
        if self.app.server == None:
            title ='No server selected'
            msg = ('Connect to a server in the Setup tab '
                   'to remove libraries...')
            tmb.showinfo(parent = self.frame, title = title, message = msg)
            return
        # test if it is racconized
        if not self.app.server.properties['ready']:
            title ='Server is not ready'
            msg = ('The server has not been prepared ("racconized") yet.\n\n'
                   'Prepare it in the Setup tab and try again.')
            tmb.showinfo(parent = self.frame, title = title, message = msg)
            return
        if len(self.app.server.getLibraries()) == 0:
            title ='No libraries'
            msg = ('The server does not have libraries installed.')
            tmb.showinfo(parent = self.frame, title = title, message = msg)
            return
        try:
            s = self.ligLibPanel.listbox.curselection()[0]
            sel = self.ligLibPanel.listbox.get(s)[0]
        except:
            #print "Nothing selected, leaving..."
            return
        libname = sel[0]
        t = 'Delete library'
        m = ('The library "%s" is going to be deleted.\n\n'
               'All files on the remote server are going to be erased.\n\n'
               'Are you sure?') % libname
        w = 'warning'
        i = 'info'
        e = 'error'
        if not tmb.askyesno(parent=self.parent, title=t, message=m, icon =w):
            return
        # deselect library to be deleted if it is selected
        if len(self.app.ligand_source):
            if libname == self.app.ligand_source[0]['lib'].name:
                self.libdeselect_cb()
        reply = self.app.server.delLibrary(libname, delfiles=True)
        if reply:
            m = 'Operation completed'
            tmb.showinfo(parent = self.parent, title=t, message = m, icon = i)
        else:
            m = 'Operation was *NOT successful'
            tmb.showinfo(parent = self.parent, title=t, message = m, icon = e)
        self.app.setBusy()
        e = RaccoonEvents.ServerConnection()
        self.app.eventManager.dispatchEvent(e)
        self.app.setReady()

    def _makelocliglibrary(self):
        self.resetFrame()
        pass

    def _makeopalliglibrary(self):
        self.resetFrame()
        # option menu
        #self.libraryChooser = OptionMenuFix(f, labelpos='w', menubutton_width=40,
        #                    label_text = 'Library :',
        #                    menubutton_font = self.FONT,
        #                    menu_font = self.FONT,
        #                    command = self.chooseLibrary,
        #                    )
        #self.libraryChooser_NULL = '<no libraries>'
        #self.libraryChooser.pack()      
        pass

    def chooseLibrary(self):
        pass
        
    def _populateliglibrarytoolbar(self, event=None):
        """ add ligand libraries to the pulldown menu"""
        # delete ligand library container
        try:
            self.ligLibPanel.listbox.delete(0, 'end')
        except:
            print "BB> ERROR HERE", sys.exc_info()[1]
            pass
        # deselect library, if any selected
        self.libdeselect_cb()

        if self.app.server == None:
            return
        problematic = []
        for lib in self.app.server.getLibraries():
            try:
                d = lib.info
                p = lib.info['properties']
                date = "%d/%02d/%02d %02d:%02d:%02d" % tuple(d['date'])
                atypes = ",".join(sorted(p['atypes']))
                self.ligLibPanel.listbox.insert('END', lib.name(), d['count'], date, d['format'], 
                        p['heavy'][0],  p['heavy'][1],  p['hba'][0], p['hba'][1],  
                        p['hbd'][0],  p['hbd'][1], p['mw'][0],  p['mw'][1], 
                        p['tors'][0],  p['tors'][1], atypes )
            except:
                problematic.append(lib)
        if len(problematic):
            t = 'Library error'
            i = 'warning'
            m = ('%d libraries on the server had problems '
                 'and cannot be imported') % len(problematic)
            try:
                libnames = ''
                for l in problematic:
                    libnames += "- %s \n"  % l.name()
                m += ':\n\n' + libnames
            except:
                m += "."
            m += ('\n\nCheck config and data files in '
                  'the Raccoon directory on the server '
                  '(i.e. ~/raccooon/libraries/)')
            tmb.showinfo(parent=self.ligLibPanel.listbox, title=t, message=m, icon=i)


class LibraryManagerWin(rb.RaccoonDefaultWidget):
    """ class to create new libraries for receptors or ligands"""
    def __init__(self, app, parent=None, _type ='ligand', mode ='add' ):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.app = app
        self._ligand_list = []
        self._register = {} # given a filename returns the name in LigBook
        self._type = _type  # ligand, receptor
        self.initIcons()
        self.makewin()

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'package.png'
        self._ICON_package = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'system.png'
        self._ICON_sys = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'open.png'
        self._ICON_open = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'remove.png'
        self._ICON_remove = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'removex.png'
        self._ICON_remove = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'upload.png'
        self._ICON_upload = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))


    def makewin(self):
        """ """
        self.win = Pmw.MegaToplevel(master = self.parent, title = 'Library Manager')
        topbar = tk.Frame(self.win.interior())
        tk.Label(topbar, text='Add files to create a new %s library...' % self._type, font=self.FONT, 
            compound='left', image = self._ICON_package).pack(anchor='w',side='left',pady=5, expand=1,fill='x')
        topbar.pack(anchor='n', side='top',expand=0, fill='x',padx=5, pady=1)
###        # settings button # XXX DISABLED
###        b = tk.Button(left_tbar, image= self._ICON_sys, **self.BORDER)
###        b.pack(anchor='n', side='top',expand=0, fill='x')
        self.center = Pmw.Group(self.win.interior(), tag_text = 'Local files [ 0 ]', tag_font=self.FONTbold)

        left_tbar = tk.Frame(self.center.interior())
        b = tk.Button(left_tbar, text='', image=self._ICON_open, **self.BORDER)
        b.pack(anchor='n', side='top',expand=0, fill='x')
        addlig_items = [ ['Add ligands'],
                         ['Import files...', 'normal', self.openfiles],
                         [],
                         ['Scan directory...', 'normal', self.open_dirs],
                         ['Scan directory (recursively)...', 'normal', self.open_dirs_recursive],
                        ]
        menu = rb.RacMenu(b, addlig_items, toolbar=left_tbar)

        b = tk.Button(left_tbar, text='[X]', image=self._ICON_remove, **self.BORDER)
        b.pack(anchor='n', side='top',expand=0, fill='x', pady=1)

        addlig_items = [ ['Remove ligands'],
                         ['Remove selected', 'normal', self.delete],
                         ['Remove all', 'normal', self.delete_all],
                        ]
        menu = rb.RacMenu(b, addlig_items, toolbar=left_tbar)

        left_tbar.pack(anchor='w', side='left', expand=0,fill='y',pady=2,padx=2)

        self.fmanager = Pmw.ScrolledListBox(self.center.interior(), listbox_font=self.FONT,
            listbox_selectmode='extended')
        self.fmanager.pack(expand=1, fill='both', anchor='n', side='top',padx=2, pady=1)
        delkey = CallbackFunction(self.delete, **{'nuke':False})
        self.fmanager.component('listbox').bind('<Delete>', delkey)

        self.uploadButton = tk.Button(self.center.interior(), text='Upload...', width=400,
            image=self._ICON_upload, compound='left', command=self.ask_upload,
            font=self.FONT, state='disabled', **self.BORDER)
        self.uploadButton.pack(anchor='s', side='bottom', expand=0, fill='x',padx=2, pady=2)

        self.center.pack(expand=1, fill='both', side='left',anchor='n',padx=3)

        right = tk.Frame(self.win.interior())
        b6 = tk.Button(right, text='Close', command=self.destroy, font=self.FONT, **self.BORDER)
        b6.pack(anchor='s', side='bottom',expand=1,fill='x')
        right.pack(anchor='e', side='bottom', expand=0, fill='y', pady=6,padx=5)
        self.win.activate()


    def _file_checker(self, flist):
        """query the Raccoon engine to check if files are acceptable
            and generate a minireport...?

            then proceed to adding them to the list
        """
        table = { 'rec' : 'receptors', 'lig' : 'ligands', 'flex' : 'flex.residues',
            'error' : 'errors/duplicates', 'result' : 'result files', 'empty' : 'empty file'}
        # response = self.app.engine.addLigandList(flist)
        if not flist:
            return 
        func = self.app.engine.addLigandList
        func_kwargs = {'filelist': flist }
        m = ('Checking %s potential ligands...' % len(flist))
        self.app.setBusy()
        progressWin = rb.ProgressDialogWindowTk(parent = self.win.interior(), 
                function = func, func_kwargs = func_kwargs, 
                title ='Importing ligands', message = m,
                operation = 'checking ligand files',
                image = self._ICON_open, autoclose=True, progresstype='percent')
        self.app.setReady()
        progressWin.start()
        response = progressWin.getOutput()
        if response == None:
            # response = {'accepted': [], 'rejected': [], 'receptor' : []}
            t = 'No ligands'
            m = ('No ligands have been found')
            i = 'info'
            tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
            return 
        if progressWin._STOP or (not progressWin._COMPLETED):
            if not len(response['accepted']):
                return
            t = 'Importing ligands'
            m = ('The ligand checking has not been completed.\n'
                 'Do you want to process %d ligands found so far?')
            m = m % len(response['accepted'])
            i = 'info'
            if not tmb.askyesno(parent=self.parent, title=t, message=m, icon=i):
                return 
        accepted = response['accepted']
        self.addfiles(accepted)
        for f in accepted:
            self._register[f[0]] = f[1] # RaccoonEngine.addLigandList -> accepted.append(f, response['name'])
        rejected = response['rejected']
        def close(event=None):
            win.destroy()
        win = Pmw.Dialog(self.win.interior(), title='Report', 
            buttons = ('Close',), command = close)
        bbox = win.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)
        w = tk.Frame(win.interior(), bg='white', **self.BORDER)
        tk.Label(w, text='Accepted :', justify='left',anchor='e', font=self.FONTbold,
            bg='white').grid(row = 1, column = 1, sticky='we')
        tk.Label(w, text=len(accepted), justify='left', font=self.FONT, bg='white', 
            anchor='e').grid(row = 1, column = 2, sticky='we')
        tk.Frame(w,height=2,width=1,bd=1,relief='sunken').grid(row=3,column=0,sticky='we', 
            columnspan=13)
        tk.Label(w, text='Problematic ', justify='left',anchor='e', font=self.FONTbold, 
            bg='white').grid(row = 4, column = 1, sticky='we')
        r = 5
        for e in rejected.keys():
            msg = table.get(e, 'unknown')
            tk.Label(w, text=msg+" :", justify='left', anchor='e',font=self.FONT, 
                bg='white').grid(row = r, column = 1, sticky='we')
            tk.Label(w, text=len(rejected[e]), justify='left', font=self.FONT, 
                bg='white').grid(row = r, column = 2, sticky='we')
            r+=1
        w.pack(expand=1,fill='both', padx=10, pady=10, ipadx=5, ipady=5)
        win.activate() #$geometry='centerscreenalways')

    def addfiles(self, flist):
        """ add files to the lisbox and the self._ligand_list"""
        fnames = [ x[0] for x in flist ]
        for f in fnames:
            self._ligand_list.append(f)
            #self.fmanager.insert('end', f)
            self._update_count()
        self.fmanager.setlist(self._ligand_list)

    def openfiles(self, event=None):
        """ add files"""
        title = 'Select one or more %s files...' % self._type

        ## filetypes = [("Supported ligand formats", ("*.pdbqt", "*.mol2", "*.pdb" )), # XXX include case-sensitive alternate
        ##             ("PDBQT", "*.pdbqt"), ("PDB", "*.pdb"), ("Mol2", "*.mol2"), 
        ##             ("Any file type...", "*")]        
        
        filetypes = [("Supported ligand formats", ("*.pdbqt","*.PDBQT" )),
                     ("PDBQT", ("*.pdbqt", "*.PDBQT")), ("Any file type...", "*")]        
        files = tfd.askopenfilename(parent=self.win.interior(), title = title,
            filetypes = filetypes, multiple = 1)
        files = self._listfixer(files)
        if len(files):
            self._file_checker(files)

    def open_dirs_recursive(self, event=None):
        """call self.add_dirs with recursive mode"""
        self.open_dirs(recursive=True)

    def open_dirs(self,event=None, recursive=False):  
        """ scan dir(s) optionally recursively"""
        title = 'Select a directory to scan'
        if recursive:
            title += ' recursively'
        dirname = tfd.askdirectory(parent=self.win.interior(), title = title, mustexist=True)
        if dirname:
            # b = tk.Button(left_tbar, text='', image=self._ICON_open, **self.BORDER)
            self.app.setBusy()
            m = ('Scanning path: %s' % dirname)
            files = []
            func = hf.pathToList
            func_kwargs = {'path':dirname, 'pattern' :'*.pdbqt', 'recursive' : recursive}
            progressWin = rb.ProgressDialogWindowTk(parent= self.win.interior(),
                function = func, func_kwargs = func_kwargs, title ='Searching for ligands', 
                    message = m, operation = 'ligands scanning',image = self._ICON_open, autoclose=True)
            progressWin.start()
            self.app.setReady()
            files = progressWin.getResults()
            if files == []:
                t = 'Searching for ligands'
                m = ('No files found.')
                i = 'info'
                tmb.showinfo(parent=self.win.interior(), title=t, message=m, icon=i)
                return 
            if progressWin._STOP or not progressWin._COMPLETED:
                t = 'Searching for ligands'
                m = ('The ligand search has not been completed.\n'
                     'Do you want to process %d files found so far?')
                m = m % len(files)
                i = 'info'
                if not tmb.askyesno(parent=self.win.interior(), title=t, message=m, icon=i):
                    return 
            self._file_checker(files)
    
    def delete(self, event=None, nuke=False):
        """ delete selected or all ligands"""
        if nuke:
            self.fmanager.setlist(())
            del self._ligand_list[:]
            self.app.engine.removeLigands()
            del self._register
            self._register = {}
        else:
            try:
                lig_sel = self.fmanager.getcurselection()# [0]
            except:
                return
            for lig in lig_sel:
                idx = self._ligand_list.index(lig)
                self._ligand_list.pop(idx)
                name = self._register.pop(lig)
                self.app.engine.removeLigands([name])
            self.fmanager.setlist(self._ligand_list)
        self._update_count()
    
    def delete_all(self, event=None):
        if len(self._ligand_list) == 0:
            return
        msg = ('%d ligands are going to be removed' 
               'from the list.\n\nContinue?') %  len(self._ligand_list)
        title = 'Warning'
        icon = 'warning'
        if not tmb.askyesno(parent = self.win.interior(), title=title, message = msg, icon=icon):
            return
        self.delete(nuke=True)


    def _update_count(self, event=None):
        """ set the label of number of items"""
        self.center.configure(tag_text = 'Local files [%d]' % len(self._ligand_list))
        if len(self._ligand_list):
            self.uploadButton.configure(state='normal')
        else:
            self.uploadButton.configure(state='disabled')

    def destroy(self, event=None):
        """
        """
        if len(self._ligand_list) > 0:
            msg = ('There are %d ligands selected to be uploaded.\n\n'
                    'If the Ligand manager will be closed, they '
                    'will not be uploaded to the server.\n\nContinue?') % len(self._ligand_list)
            if not tmb.askyesno(parent=self.win.interior(), title='Warning', message = msg, icon ='warning'):
                return
        self.app.engine.removeLigands()
        self.win.deactivate()


    def ask_upload(self):
        """upload to remote location"""
        if len(self._ligand_list) == 0:
            return

        def close(event=None):
            if event == 'Start':
                server = self.app.server
                # check if lib name is in use
                libname = self._lname.getvalue()
                lib = server.getLibrary(libname)

                if lib: # and lib.info['type'] == self.info['type']:
                    t = 'Name already in use'
                    m = ('There is already a %s library with the same name.\n\n'
                           'Choose a different name and try again.') % self._type
                    i = 'warning'
                    tmb.showinfo(parent=win.interior(), title=t, message=m, icon=i)
                    return
                # check directory name
                dirname = self._dname.getvalue()
                remotepath = self._remotepath.getvalue()
                fullpath = remotepath + '/' + dirname
                if server.ssh.exists(fullpath):
                    t = 'Directory exist'
                    m = ('There is already a directory with the same in the'
                         'remote path. Select a different dirname '
                           'and try again.')
                    i = 'warning'
                    tmb.showinfo(parent=win.interior(), title=t, message=m, icon=i)
                    self.app.setReady()
                    return
                # comments, if any
                comment = self._comment.get('1.0', 'end').strip()
                win.destroy()
                self.app.setBusy()
                self.run_upload(name = libname, 
                    dirname = dirname, 
                    remotepath = remotepath, 
                    comment = comment)
                # once files habe been uploaded, clean up the engine from used files
                self.app.engine.removeLigands()
                self.app.setReady()
            else:
                win.destroy()
                self.app.setReady()

        def makedirname(event=None):
            """ ButtonRelease """
            chars = hf._allowedfilenamechars()
            text = self._lname.getvalue()
            if not len(text):
                self._dname.setvalue('')

            valid = [ x for x in text if x in hf._allowedfilenamechars()]
            valid = "".join(valid).lower() 
            self._dname.setvalue(valid)

        def setdefaultremote(event=None):
            self._remotepath.setvalue( self.app.server.getLibraryPath() )

        #settings = { 'split' : 1000, 
        #    }
        win = Pmw.Dialog(self.win.interior(), title = 'Upload library', buttons = ('Start','Cancel'), 
                command=close)
        w = win.interior()
        bbox = win.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)
        w.pack_configure(ipadx=10, ipady=10)

        tk.Label(w, text=' ', image=self._ICON_upload, anchor='n', font=self.FONTbold).grid(row=0,
            column=0, sticky='we', columnspan = 3)
        tk.Label(w, text='Library name', anchor='e', font=self.FONT).grid(row=1, column=1, sticky='e')
        self._lname = Pmw.EntryField( w, validate = {'min':1,'minstrict':0}, entry_width=30, 
            entry_font=self.FONT)
        self._lname.component('entry').bind('<KeyRelease>', makedirname)
        self._lname.grid(row=1, column=2,sticky='w',columnspan=1)

        tk.Label(w, text='Remote path', anchor='e', font=self.FONT).grid(row=3, column=1, sticky='e')
        self._remotepath = Pmw.EntryField( w, validate = {'min':1,'minstrict':0}, 
            entry_width=30, entry_font=self.FONT)
        self._remotepath.grid(row=3, column=2,sticky='w',columnspan=1)
        tk.Button(w, text='D', command=setdefaultremote,image=self._ICON_default,   
            **self.BORDER).grid(row=3, column=3, sticky='w')

        # FIXME probably useless, this should be hidden to the user!
        #tk.Label(w, text='Directory name', anchor='e').grid(row=5, column=1, sticky='e', 
        #    entry_font=self.FONT)
        self._dname = Pmw.EntryField( w, validate = hf.validateFname, entry_width=30)
        #self._dname.grid(row=5,column=2, sticky='w', columnspan=1)
        tk.Label(w, text='Comments', anchor='e', font=self.FONT).grid(row=6, column=1, sticky='e')
        self._comment = hf.TextCopyPaste( w, bg='white', height=10, width=30, font=self.FONT)
        self._comment.grid(row=6,column=2, sticky='w')
        setdefaultremote()
        win.activate() # geometry='centerscreenalways' )

    def run_upload(self, name, dirname, remotepath, comment=None):
        """ """
        #    self.run_upload(name = libname, dirname = dirname, remotepath = remotepath)
        def _go(event=None):
            #server.debug = True
            #libobj.debug= True
            self.app.setBusy()
            if comment:
                libobj.info['comment'] = comment
            libobj.upload( dirname, remotepath, autoregister=0, bg = True)
            self.RUNNING = True
            self._stopclosebutton.configure(text= 'Stop', command=stop)
            status = server.transfer.progress(percent=1)

            while status < 100.:
                if server.transfer._STOP: break
                status = server.transfer.progress(percent=1)
                pc_var.set(status)
                self.bar.update()
                time.sleep(0.2)
            self.RUNNING = False

            libobj.debug = True # DEBUG 
            if server.transfer._status['completed']:
                # EVENT trigger the event refresh of server list
                #idxfile = remotepath + '/'+ dirname +'/'+'library.db'
                #idxfile = 'library.db'
                self._statuslab1.configure(text='Generating index file')
                self._statuslab2.configure(text='...saving...')
                libobj.saveIndex()
                self._statuslab1.configure(text='Registering library to Library Index')
                self._statuslab2.configure(text='...ongoing...')
                libobj.register()
                self._statuslab1.configure(text='\nLibrary upload completed!')
                self._statuslab2.configure(text=' ')
                del self._ligand_list[:]
                self.delete(nuke=True)
                e = RaccoonEvents.ServerConnection()
                self.app.eventManager.dispatchEvent(e)
            else:
                error = server.transfer_status['error']
                self._statuslab1.configure(text='Error trasnferring files!')
                self._statuslab2.configure(text=error)
            self._stopclosebutton.configure(text= 'Close', command=forceclose)
            self.app.setReady()

        def close(event=None):
            if event == None:
                #print "probably clicking on the corner..."
                return
            win.destroy()

        def stop(event=None):
            t = 'Stop transfer'
            m = 'The transfer is incomplete: do you want to stop it?'
            if not tmb.askyesno(parent = win.interior(), title=t, message=m):
                return
            server.transfer.stop()
            self._stopclosebutton.configure(text= 'Close', command=close)

        forceclose = CallbackFunction(close, True)


        ## print ">> adding ligands to lib object"
        # threaded files scanning...
        server = self.app.server
        libobj = RaccoonLibraries.LigandLibrary( server, name = name )
        libobj.options['split'] = 1000
        func = libobj.addLigands
        func_kwargs = {'ligands' : self._ligand_list }
        m = ('Extracting ligand properties...' )
        self.app.setBusy()
        progressWin = rb.ProgressDialogWindowTk(parent = self.parent,
                function = func, func_kwargs = func_kwargs, 
                title ='Ligand library', message = m, 
                operation = 'ligand properties extraction',
                image = self._ICON_open, autoclose=True, 
                progresstype='percent')
        progressWin.start()
        problematic = progressWin.getResults()
        if problematic == None: problematic = [] # normalize data structure
        self.app.setReady()
        #if response == None:
        #libobj.addLigands(self._ligand_list) # XXX TODO FIXME 

        win = Pmw.MegaToplevel(master = self.win.interior(), title = 'Library manager')
        win.userdeletefunc(close)
        win.component('hull').configure(width=600, height=400)
        
        fullpath = remotepath + '/' + dirname
        self._statuslab1 = tk.Label(win.interior(), text = 'Transferring files...', font=self.FONTbold)
        self._statuslab1.pack(expand=0, fill='x', anchor='w', side='top')
        self._statuslab2 = tk.Label(win.interior(), text = 'Destination: %s' % fullpath, font=self.FONT)
        self._statuslab2.pack(expand=0, fill='x', anchor='w', side='top')
        pc_var = tk.DoubleVar(value=0.)
        self.bar = hf.ProgressBar(win.interior(), pc_var)
        self.bar.pack(expand=0, fill='none', anchor='n', side='top',padx=5, pady=3)
        tk.Frame(win.interior(),height=2,width=1,bd=1,relief='sunken').pack(expand=0, fill='x', anchor='w', side='top')
        self._stopclosebutton = tk.Button(win.interior(), text='STOP', font=self.FONT)
        self._stopclosebutton.pack(expand=0, fill='none', anchor='s', side='bottom')

        win.interior().after(50, _go)
        win.activate() # geometry='centerscreenalways' )
            

