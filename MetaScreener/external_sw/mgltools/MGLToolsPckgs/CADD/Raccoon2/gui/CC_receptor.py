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


import os, Pmw, glob
from PmwOptionMenu import OptionMenu as OptionMenuFix

import Tkinter as tk
import tkMessageBox as tmb
import tkFileDialog as tfd
from PIL import Image, ImageTk

import TkTreectrl

# mgl modules
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction #as cb


class ReceptorTab(rb.TabBase, rb.RaccoonDefaultWidget):

    def __init__(self, app, parent, debug=False):
        rb.TabBase.__init__(self, app, parent, debug = False)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.resource = self.app.resource
        self.dockengine = self.app.dockengine
        #self.app.eventManager.registerListener(RaccoonEvents.SetResourceEvent, self.handleResource)
        self.initIcons()        
        self.makeInterface() 


    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH

        f = icon_path + os.sep + 'system.png'
        self._ICON_sys = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'water.png'
        self._ICON_water = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'floppy.png'
        self._ICON_floppy = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'open.png'
        self._ICON_open = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'add.png'
        self._ICON_add = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'remove.png'
        self._ICON_rem = ImageTk.PhotoImage(Image.open(f))

    def makeInterface(self, resource=None):
        """ """
        self.makeInterfaceSsh()
        if resource == 'local':
            self.makeInterfaceLocal()
        elif resource == 'ssh':
            self.makeInterfaceSsh()
        elif resource == 'opal':
            self.makeInterfaceOpal()        


    def makeInterfaceLocal(self):
        self.makeInterfaceSsh()
        """ """
        pass

    def openfiles(self, event=None, files = [], quiet=False):
        """ ask for one or more rec files"""
        title = 'Select receptor file(s), flex res...' 
        filetypes = [("Supported ligand formats", ("*.pdbqt","*.PDBQT" )),
                     ("PDBQT", ("*.pdbqt", "*.PDBQT")), ("Any file type...", "*")]        
        if not files:
            files = tfd.askopenfilename(parent=self.frame, title = title, filetypes = filetypes, multiple = 1)
            files = self._listfixer(files)
        if len(files):
            self._file_checker(flist=files, quiet=quiet) 

    def opendir(self, event=None, recursive=False):
        """ scan dir(s) optionally recursively"""
        title = 'Select a directory to scan'
        if recursive:
            title += ' recursively'
        # add a GUI feedback:
        # - GUIvar 
        # - progress bar
        # progress = tk.StringVar('Processing 
        #
        dirname = tfd.askdirectory(parent=self.frame, title = title, mustexist=True)
        if dirname:
            files = hf.pathToList(dirname, pattern = '*.pdbqt', recursive = recursive) # XXX progress var here...
            #files.append(hf.pathToList(dirname, pattern = '*.PDBQT', recursive = recursive)) # XXX ?
            #hf.writeList('FOUND.log', files, addNewLine=1)
            if len(files):
                self._file_checker(files)

    def opendir_recursive(self, event=None):
        """ """
        self.opendir(recursive=True)

    def addfiles(self, accepted):
        """ """
        for rec in accepted:
            r = rec[0]
            rec_data = self.app.engine.RecBook[r]
            types = ""
            unk=''
            flex_res = '[no]'
            chains = ''
            for a in sorted(rec_data['atypes']):
                types+=" %s" % a
            types = types.strip()
            for a in sorted(rec_data['atypes_unknown']):
                unk += ' %s' % a
            unk = unk.strip()
            if rec_data['is_flexible']: # in rec_data.keys():
                #print "ISFLEXI"
                flex_res = " ".join(rec_data['flex_res'])
            chains = " ".join(rec_data['chains'])
            self.recFileManager.listbox.insert('end',rec_data['name'], chains, 
                len(rec_data['residues']), flex_res, types, unk, rec_data['filename'])
            # EVENT
            # XXX TEMPORARY
            self.app.configTab.setReceptorList()
            #elif action=='del':
                #print "FIND A WAY TO DELETE SOMETHING FROM self.tab2.recContainer"
                # find the index!
                #self.tab1.ligContainer.listbox.delete(0,END)
                # XXX Obsolete
            #    pass        
        e = RaccoonEvents.UserInputRequirementUpdate('rec')
        self.app.eventManager.dispatchEvent(e)
        self.updatereccount()

    ### 
    def deletefiles(self, nuke=False, event=None):
        if nuke == True:
            # EVENT UPDATES
            self.app.engine.removeReceptors()
            self.recFileManager.listbox.delete(0,'end')
            self.updatereccount()
        else:
            try:
                s = self.recFileManager.listbox.curselection()[0]
                sel = self.recFileManager.listbox.get(s)[0]
            except:
                #print "BB_REC> Nothing selected, leaving..."
                return
            name = sel[0]
            self.app.engine.removeReceptors([name])
            self.recFileManager.listbox.delete(s)
        e = RaccoonEvents.UserInputRequirementUpdate('rec')
        self.app.eventManager.dispatchEvent(e)
        self.updatereccount()

    def deleteallfiles(self):
        c = len(self.app.engine.RecBook.keys())
        if c == 0:
            return
        t = 'Warning'
        m = 'All %d receptors are going to be deleted\n\nAre you sure?' % c
        if not tmb.askyesno(parent=self.frame, title=t, message=m, icon='warning'):
            return
        self.deletefiles(nuke=True)


    def updatereccount(self):
        """update labels and list in the config panel in the """
        # update the count of accepted receptors
        msg = 'Accepted structures [ %s ]' % len(self.app.engine.RecBook) 
        self.recGroup.configure(tag_text = msg)
        ## XXX  THIS IS THE CONFIG PANEL ENTRY
        ## self.GUI_rec_list_container.insert('end', rec_data['name'])
        e = RaccoonEvents.ReceptorListChange()
        self.app.eventManager.dispatchEvent(e)





    def _file_checker(self, flist, quiet=False):
        """query the Raccoon engine to check if files are acceptable
            and generate a minireport...?

            then proceed to adding them to the list
        """
        table = { 'rec' : 'receptors', 'lig' : 'ligands', 'flex' : 'flex.residues',
            'error' : 'errors/duplicates', 'is_ligand': 'ligands'}

        response = self.app.engine.addReceptorList(flist)
        accepted = response['accepted']
        self.addfiles(accepted)
        rejected = response['rejected']
        #del rejected['rec']

        if not quiet:
            def close(event=None):
                win.destroy()
                
            win = Pmw.Dialog(self.frame, title='Report', 
                buttons = ('Close',), command = close)
            # XXX
            bbox = win.component('buttonbox')
            for i in range(bbox.numbuttons()):
                bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)

            w = tk.Frame(win.interior(), bg='white', **self.BORDER)
            tk.Label(w, text='Accepted :', justify='left',anchor='e', font=self.FONTbold, bg='white').grid(row = 1, column = 1, sticky='we')
            tk.Label(w, text=len(accepted), justify='left', font=self.FONT, bg='white', anchor='w').grid(row = 1, column = 2, sticky='we')
            tk.Frame(w,height=2,width=1,bd=1,relief='sunken').grid(row=3,column=0,sticky='we', columnspan=13)
            if len(rejected):
                tk.Label(w, text='Problematic ', justify='left',anchor='e', font=self.FONTbold, bg='white').grid(row = 4, column = 1, sticky='we')
                r = 5
                reasons = {}
                for fail in rejected: #.keys():
                    #f = fail[0]
                    e = fail[1]
                    if e in reasons.keys():
                        reasons[e] += 1
                    else:
                        reasons[e] = 1
                for err in sorted(reasons.keys()):
                    msg = "%s :" % table.get(err, 'unknown')
                    tk.Label(w, text=msg, justify='left', anchor='e',font=self.FONT, bg='white').grid(row = r, column = 1, sticky='we')
                    tk.Label(w, text=reasons[e], justify='left', anchor='w',font=self.FONT, bg='white').grid(row = r, column = 2, sticky='we')
                    r+=1
            w.pack(expand=1,fill='both', padx=10, pady=10, ipadx=5, ipady=5)
            win.activate()


    def makeInterfaceSsh(self):
        """ """
        bset = { 'bg' : '#969b9d'  } # 'width' : 22, 'height': 22, 'relief' : 'raised'}
        bset = {}
        bset.update(self.BORDER)
        self.resetFrame()
        self.recGroup = Pmw.Group(self.frame, tag_text = 'Accepted structures [ 0 ]', tag_font = self.FONTbold)

        # toolbar
        toolb = tk.Frame(self.recGroup.interior())

        if self.sysarch == 'Windows':
            bwidth = 54
        else:
            bwidth = 32
        ###### add button
        # make button
        b = tk.Button(toolb, text='Add...', compound='top', image = self._ICON_add, width=bwidth, font=self.FONTbold, **bset )
        b.pack(anchor='n', side='top')
        # make menu items
        addrec_items = [ ['Add receptors'],
                         ['Import files...', 'normal', self.openfiles],
                         [],
                         ['Scan directory...', 'normal', self.opendir],
                         ['Scan directory (recursively)...', 'normal', self.opendir_recursive],
                         # [],
                         # ['Select structure from history...', 'normal', self.opendir],
                         ]
        # make menu
        menu = rb.RacMenu(b, addrec_items, toolbar=toolb)

        ###### add button
        # make button
        b = tk.Button(toolb, text='Remove...', compound='top', image = self._ICON_rem, width=bwidth, font=self.FONTbold, **bset )
        b.pack(anchor='n', side='top', pady=1)
        # make menu items
        addrec_items = [ ['Remove receptors'],
                         ['Remove selected', 'normal', self.deletefiles],
                         ['Remove all', 'normal', self.deleteallfiles],
                         ]
        # make menu
        menu = rb.RacMenu(b, addrec_items, toolbar=toolb)
        # 
        #tk.Button(toolb, text='Settings\n&\nAlignment...', compound='top', image = self._ICON_sys, width=32, 
        #    font=self.FONTbold, **bset ).pack(anchor='n', side='top',pady=1)
        toolb.pack(side='left', anchor='w', expand=0, fill='y',pady=0)

        # files manager
        self.recFileManager = TkTreectrl.ScrolledMultiListbox(self.recGroup.interior(), bd=2)
        self.recFileManager.listbox.config(bg='white', fg='black', font=self.FONT,
                   columns = ('name', 'chains', 'res.', 'flex_res', 
                              'atom types', 'unk.types', 'filename'),
                   selectmode='extended',
                              )
        delkey = CallbackFunction(self.deletefiles, {'nuke':False})
        self.recFileManager.listbox.bind('<Delete>', delkey)

        self.recFileManager.pack(anchor='w', side='left', expand=1, fill='both')

        self.recGroup.pack(anchor='n', side='top', expand=1, fill='both')

        self.frame.pack(expand=1, fill='both',anchor='n', side='top')

    def makeInterfaceOpal(self):
        self.makeInterfaceSsh()
        """ """
        pass
