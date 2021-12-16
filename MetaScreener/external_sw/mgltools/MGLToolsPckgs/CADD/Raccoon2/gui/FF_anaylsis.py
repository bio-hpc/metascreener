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


# Raccoon stuff
import CADD.Raccoon2
import CADD.Raccoon2.HelperFunctionsN3P as hf
import RaccoonBasics as rb
import RaccoonEvents
import RaccoonPmvCamera 
import TkTreectrl
import DebugTools
import RaccoonResTree
import EF_resultprocessor
import RaccoonFilterInteract
import os, Pmw, glob, sys
from PmwOptionMenu import OptionMenu as OptionMenuFix

import Tkinter as tk
import tkMessageBox as tmb
import tkFileDialog as tfd
from PIL import Image, ImageTk

# mgl modules
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction #as cb
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

from SlidingRange import RangeSlider

from MolKit import Read
from MolKit.pdbWriter import PdbWriter
import shutil

class AnalysisTab(rb.TabBase, rb.RaccoonDefaultWidget):
    
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

        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))

    def makeInterface(self, resource=None):

        self.notebook = Pmw.NoteBook(self.parent)
        self.tabs = {}
        for tab in ['Data source', 'Visualization', 'Export']:
            self.tabs[tab] = self.notebook.add(tab)
            self.notebook.component(tab+'-tab').configure(font=self.FONT)
        self.notebook.pack(expand=1,fill='both')

        self.dataTab = DataSourceTab(self.app, self.tabs['Data source'])

        self.visualTab = ViewerTab(self.app, self.tabs['Visualization'])

        self.exportTab = ExportTab(self.app, self.tabs['Export'])




class DataSourceTab(rb.TabBase, rb.RaccoonDefaultWidget):
    
    def __init__(self, app, parent, debug=False):
        rb.TabBase.__init__(self, app, parent, debug = False)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.resource = self.app.resource
        self.dockengine = self.app.dockengine
        #self.app.eventManager.registerListener(RaccoonEvents.SetResourceEvent, self.handleResource)
        
        #self.initIcons()
        self.makeInterface()

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'system.png'
        self._ICON_sys = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'basket.png'
        self._ICON_note = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'water.png'
        self._ICON_water = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'floppy.png'
        self._ICON_floppy = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'open.png'
        self._ICON_open = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))

    def makeInterface(self):
        #tk.Label(self.frame, text="TERRIBLE THINGS ARE GOING TO HAPPEN HERE\n\n(DATA SOURCE)").pack(expand=0, fill='x')

        self.pane = Pmw.PanedWidget(self.frame, orient='horizontal', handlesize=-1,
            separatorthickness=10, separatorrelief='raised', )
        self.left = self.pane.add('info', min=3, size=350)
        self.right =  self.pane.add('viewer', min=3, size=10)
        handle = self.pane.component('handle-1')
        sep = self.pane.component('separator-1')
        handle.place_forget()
        handle.forget()
        handle.pack_forget()
        handle.grid_forget()        

        # manage separator cosmetics
        sep.configure(bd =2, #bg = '#999999'
            highlightthickness=1, highlightbackground='black', highlightcolor='black')
        # separator for rearranging 
        spacer = tk.Frame(self.right, width=8)
        spacer.pack(expand=0, fill='y',side='left', anchor='w')
        # nail handle
        tk.Frame(sep,height=40,width=4,bg='#fffeee',relief='sunken',bd=1,highlightbackground='black',
            highlightthickness=1).pack( anchor='center', padx=2,pady=2,side='left',expand=0,fill=None)


        # results manager
        self.ResManager =  ResultsManager(self.left, self.app)
        self.ResManager.pack(expand=1,fill='both',side='top', anchor='n',padx=5,pady=0)


        # filter manager
        self.FilterManager = FilterManager(self.right, app=self.app)
        #self.FilterManager.pack(expand=1, fill='both', side='top', anchor='n', padx=5, pady=5)
        self.FilterManager.pack(expand=0, fill='y', side='top', anchor='w', padx=5, pady=5)

        self.pane.pack(expand=1,fill='both')
        self.pane.setnaturalsize()
        #self.pane.updatelayout()

        self.frame.pack(expand=1, fill='both')

        self.app.x = self.setOptimalSize
        #self.setOptimalSize()


    def setOptimalSize(self):
        """ force app.master to resize view to show everything"""
        self.pane.update_idletasks()
        wact = int(self.right.winfo_width())
        hact = int(self.right.winfo_height())
        wreq = int(self.right.winfo_reqwidth())
        hreq = int(self.right.winfo_reqheight())
        res, offset = self.app.master.geometry().split("+", 1)
        x, y = map(int, res.split("x"))
        org_x, org_y = x,y
        deltax = wreq - wact
        deltay = hreq - hact
        x += deltax
        y += deltay
        newgeom = "%sx%s+%s" % (x,y,offset)
        self.app.master.geometry(newgeom)
        





class ResultsManager(rb.RaccoonDefaultWidget, DebugTools.DebugObj,  Pmw.Group):
    """ items manager to add/remove results to the current session"""
    def __init__(self, parent, app, debug=False):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        DebugTools.DebugObj.__init__(self, debug)
        Pmw.Group.__init__(self, self.parent, tag_text = 'Docking results', tag_font=self.FONTbold)
        self.app = app
        self.processor = self.app.resultsProcessor
        self.initIcons()
        self.makeInterface()

        self.app.eventManager.registerListener(RaccoonEvents.ResultsImportedDeleted, self.updateCountLabel)


    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH

        f = icon_path + os.sep + 'open.png'
        self._ICON_open = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'tree.png'
        self._ICON_tree = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'removex.png'
        self._ICON_remove = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))

    def makeInterface(self):
        """ do the actual widget placement"""
        # toolbar
        f = tk.Frame(self.interior())
        # select from tree
        #b1 = tk.Button(f, image=self._ICON_tree, command=self.selectFromTree, **self.BORDER)
        #b1.pack(anchor='w',side='left')
        # add log/scan dirs
        b2 = tk.Button(f, image=self._ICON_open, **self.BORDER)
        b2.pack(anchor='w',side='left',padx=0)
        items = [ ['Add results'],
                  ['Select downloaded results...', 'normal', self.selectFromTree ],
                  ['Import from summary log file...', 'normal', self.importLogAskRec ],
        #          ['Process directory (AD)...', 'normal', self.processDirAD ], 
                  ['Process directory (Vina)...', 'normal', self.processDirVINA ],  
                  ] 
        menu = rb.RacMenu(b2, items, toolbar=f, placement='under')
        # remove
        b3 = tk.Button(f, image=self._ICON_remove, **self.BORDER)
        b3.pack(anchor='w',side='left', padx=1)
        items = [ ['Remove results'],
                  ['Remove selected', 'normal', self.removeSelected ],
                  ['Remove all...', 'normal', self.removeAll ], ] 
        menu = rb.RacMenu(b3, items, toolbar=f, placement='under')

        f.pack(expand=0, fill='x', side='top', anchor='n',padx=2)
        # listbox
        self.resmanager = TkTreectrl.ScrolledMultiListbox(self.interior(), bd=2)
        self.resmanager.listbox.config(bg='white', fg='black', font=self.FONT,
              columns = ('name', 'receptor', 'lig.count', 'E.best', 'E.worst',))
        self.resmanager.listbox.config(**self.BORDER)
        self.resmanager.pack(expand=1, fill='both', anchor='n', side='top')
        #  total result counts label
        f = tk.Frame(self.interior())
        tk.Label(f, text='Total docking results:', anchor='w', 
            font=self.FONTbold).pack(side='left', anchor='w',padx=2)
        self.rescountLabel = tk.Label(f, text='0', anchor='w', bg='white', font=self.FONT, **self.BORDER)
        self.rescountLabel.pack(side='left',anchor='w',expand=1,fill='x',padx=2)
        f.pack(expand=0,fill='x', anchor='s', side='bottom',pady=2)


    def updateCountLabel(self, event=None):
        """ update the counter of current ligands"""
        self.rescountLabel.configure(text = "%s" % self.app.countResults() )


    def selectFromTree(self, event=None):
        """ select downloaded results from the project tree"""
        #print "SELECTING FROM TREE"
        parent = self.resmanager.listbox
        pool = {}
        for pk, pv in self.app.history.items():
            for ek, ev in pv.items():
                for vk, vv in ev.items():
                    if vv['status'] == 'downloaded':
                        if not pool.has_key(pk):
                            pool[pk] = {}
                        if not pool[pk].has_key(ek):

                            pool[pk][ek] = {}
                        pool[pk][ek][vk] = vv
        if not len(pool.keys()):
            t = 'Downloaded results'
            i = 'info'
            m = ('No results have been downloaded yet.\n'
                 'Use the Job manager tab to download completed '
                 'results or import external results.')
            tmb.showinfo(parent = parent, title=t, icon=i, message=m)
            return

        choice = RaccoonResTree.DictTreeCheckSelector(self.resmanager.listbox, pool)
        jobs = self.getSelectedResults(choice.result) 
        #print "JOBS", jobs
        ready = []
        tobeprocessed = []
        for j in jobs:
            p,e,v = j
            info = self.app.history[p][e][v]
            summary = info['summary']
            #print "SSMERIAN", summary, "====", p, e, v
            if summary:
                summary = os.path.join(self.app.getJobDir((p,e,v)), summary)  
                if os.path.exists(summary):
                    ready.append(summary)
            else:
                tobeprocessed.append( (p,e,v) )
        if len(tobeprocessed):
            t = 'Unprocessed results'
            i = 'info'
            m = ('%d results do not have a summary file '
                 'and need to be processed.\n'
                 '\nContinue?' % len(tobeprocessed) )

            if not tmb.askyesno(parent=parent, title=t, message=m, icon=i):
                return
            for j in tobeprocessed:
                processed = EF_resultprocessor.ProcessResultsGui(parent=self.parent, app=self.app, job=j, auto=True)
                ready += processed

        if len(ready):
            for summary in ready:
                self.importLog(logfile=summary)



    def getSelectedResults(self, choice):
        """ expand the choice generated by DictTreeCheckSelector
            and scan the history file to get the actual
            jobs to be added to the analysis tab

            choice = [ [ prj, exp, vs ], ... ]
        """
        pool = []
        for item in choice:
            prj = item[0]
            if len(item) > 1:
                exp_pool = [ item[1] ]
            else:
                exp_pool = self.app.history[prj].keys()
            for exp in exp_pool:
                if len(item) > 2:
                    vs_pool = [ item[2] ]
                else:
                    vs_pool = self.app.history[prj][exp].keys()
                for vs in vs_pool:
                    if  self.app.history[prj][exp][vs]['status'] == 'downloaded':
                        pool.append([ prj, exp, vs ])
        return pool


    def importLogAskRec(self):
        self.importLog(askrec=True)


    def importLog(self, event=None, logfile=None, askrec=False, rec=None):
        """ import results from a log file"""
        # use the log file as name suggestion
        t = 'Import processed log file'
        ft = [("Raccoon summary log file", ("*.log")),
              ("Any file type...", "*")] 
        idir = self.app._lastdir
        p = self.resmanager.listbox
        if logfile == None:
            logfile = tfd.askopenfilename(parent=p, title=t, initialdir=idir, filetypes=ft)
        if not logfile:
            return
        logfile = os.path.normpath(os.path.expanduser(logfile))
        path = self.app._lastdir = os.path.dirname(logfile)
        name = os.path.basename(logfile)
        if name in self.app.results.keys():
            return
        if askrec:
            t = 'Select receptor filename'
            ft = [("PDBQT receptor", ("*.pdbqt")),
                      ("Any file type...", "*")] 
            rec = tfd.askopenfilename(parent=p, title=t, initialdir=idir, filetypes=ft)
            if not rec:
                return
        try:
            #data = hf.readjson(logfile)
            data = hf.readmarshal(logfile)
            for n,i in data.items():
                engine = i['data'][0]['engine']
                break
            if not self.checkDockEngineMatch(engine):
                return
            self.app.importResults(data=data, name=name, path=path, rec=rec)
            self.addResManEntry(data, name)
        except:
            e = sys.exc_info()[1]
            t = 'Error'
            i = 'error'
            m = ('Invalid Raccoon log file.\n\n[Error: %s]' % e)
            tmb.showinfo(parent = self.resmanager.listbox, 
                title=t, icon=i, message=m)

    def addResManEntry(self, data, name):
        """ add an entry in the multilistbox of results
            populating columns
        """
        eworst = -10E99
        ebest = 10E99
        for l, poses in data.items():
            i = poses['data'][0]
            ebest = min(ebest, float(i['energy']))
            eworst = max(eworst, float(i['energy']))
        rec = i['recname']
        count = len(data.items())
        self.resmanager.listbox.insert('END', name, rec, count, ebest, eworst)
            
    
    def checkDockEngineMatch(self, required):
        """ check that the selected engine matches the
            results anaylsis requested by user
        """
        # match
        if self.app.dockengine == required:
            return True
        # mismatch
        tot_results =  len(self.app.results.keys())
        if not tot_results == 0:
            # there are some results
            t = 'Docking engine mismatch'
            i = 'warning'
            m = ('The %d docking results currently'
                 'imported have been generated with '
                 'another engine.\n\n'
                 'Do you want to discard them?') % tot_results
            if not tmb.askyesno(parent=self.parent, title=t, message=m, icon=i):
                return False
        self.app.setDockEngine(required)
        return True

    def processDirAD(self, event=None):
        """ """
        # DLG/OUT hf.pathToList
        # scan for pdbqt files
        # guess recname from dir/ask for receptor filename
        # process
        # progress bar...?
        # if successful: import the generated logfile
        pass


    def processDirVINA(self, event=None, ):
        """ scan a directory for result files"""
        t = 'Select a directory of docking results'
        if not self.checkDockEngineMatch('vina'):
            return
        # set dir
        idir = self.app._lastdir
        dirname = tfd.askdirectory(parent=self.resmanager.listbox, title=t, initialdir=idir)
        if not dirname:
            return
        dirname = os.path.normpath(os.path.expanduser(dirname))
        logname = os.path.basename(dirname) + '_summary.log'
        logfile = os.path.join(dirname, logname)
        #print "LOGFILE", logfile
        self.app._lastdir = dirname
        # check previous receptor
        receptor_ok = False
        curr_recname = self.app.resultsProcessor.processor.recname
        if curr_recname:
            t = 'Receptor structure'
            i = 'info'
            m = ('Use the currently defined receptor "%s"?' % curr_recname)
            # use current
            if tmb.askyesno(parent=self.parent, title=t, icon=i, message=m):
                receptor_ok = True
        # load new receptor
        if not receptor_ok:
            receptor = self.searchReceptor(dirname) 
            if not receptor:
                return
            self.app.resultsProcessor.setReceptor(receptor)
        # scan for results
        ligs = self.searchLigandsVINA(dirname)
        if not len(ligs):
            t = 'Docking results'
            i = 'info'
            m = ('No Vina docking results have been found '
                 'in the specified directory')
            tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
            return
        if len(ligs):
            result= EF_resultprocessor.ProcessResultsGui(parent=self.parent,
                        app=self.app, ligands=ligs, logfile = logfile)
            logfile = result.logfile
            #print "RESULT.LOGFILE", result.logfile
            if os.path.isfile(logfile):
                self.importLog(logfile=logfile, rec=receptor)
            else:
                t = 'No results to import'
                m = ('The results generation failed so there are no results to import')
                i = 'error'
                tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
                return


    def searchReceptor(self, dirname=None):
        """ search for receptor in dirname and ask
            user if it fails
        """
        rec_found = hf.pathToList(dirname, pattern='*.pdbqt', recursive=False)
        receptor = None
        if len(rec_found) == 1:
            recname = os.path.basename(rec_found[0])
            t = 'Receptor structure'
            i = 'info'
            m = ('Use the receptor structure in the '
                'directory?\n\n%s' % recname)
            if tmb.askyesno(parent=self.parent, title=t, icon=i, message=m):
                receptor=rec_found[0]
        if receptor == None:
            t = 'Select receptor file'
            filetypes = [("Supported ligand formats", ("*.pdbqt","*.PDBQT" )),
                         ("PDBQT", ("*.pdbqt", "*.PDBQT")), ("Any file type...", "*")]        
            receptor = tfd.askopenfilename(parent=self.parent, title = t,
                filetypes = filetypes, initialdir=dirname)
        print "SEARCH RECEPTOR SAID", receptor
        return receptor

    def searchLigandsAD(self,dirname, pattern = '*.dlg'):
        """ scan the directory for ligand files"""
        dockfiles = hf.pathToList(dirname, recursive = True, pattern = pattern)
        files = hf.findLigandsInDlg(dockfiles, showprogress=False)
        return files

    def searchLigandsVINA(self, dirname, pattern= '*_out.pdbqt'):
        """ scan dir for vina results"""
        dockfiles = hf.pathToList(dirname, recursive = True, pattern = pattern)
        self.dprint("found %s dockfiles" % dockfiles)
        result = {}
        for d in dockfiles:
            name = os.path.basename(d).split("_out.pdbqt")[0]
            result[name] = d
        return result

    def removeSelected(self, event=None, selected=None):
        """ remove selected results"""
        if not len(self.app.results.keys()): return
        try:
            s = self.resmanager.listbox.curselection()[0]
            sel = self.resmanager.listbox.get(s)[0]
        except:
            #print "RESMAN, nothing selected"
            return
        self.resmanager.listbox.delete(s)
        self.app.deleteResults(sel[0])

    def removeAll(self, event=None):
        """ remove all results from the session"""
        if not len(self.app.results.keys()): return
        t = 'Removing all results'
        i = 'info'
        m = ('Do you want to remove all results loaded in the session?')

        if not tmb.askyesno(parent=self.resmanager.listbox, title=t, message=m, icon=i):
            return
        self.resmanager.listbox.delete(0,'end')
        self.app.deleteResults()


class FilterManager(rb.RaccoonDefaultWidget, Pmw.Group, DebugTools.DebugObj):
    """ items manager to add/remove results to the current session"""
    def __init__(self, parent, app, mode='vina', debug=False):
        rb.RaccoonDefaultWidget.__init__(self, parent)

        Pmw.Group.__init__(self, self.parent, ring_borderwidth=0) #$ tag_text = 'Filters', tag_font=self.FONTbold)
        DebugTools.DebugObj.__init__(self, debug)

        self.app = app
        self.mode = mode # define wich filters are going to be created
        
        # filters
        self.filtWidgets = {} # item.getvalues() 
        self._accepted = 0
        self._pending = None
        self._DEFAULT_FILTERSET = '<default>'
        self.filterSets = {self._DEFAULT_FILTERSET : None}
        self.initIcons()
        self.makeInterface()

        self.app.eventManager.registerListener(RaccoonEvents.FilterSetSelection, self.selFilterSet)
        self.app.eventManager.registerListener(RaccoonEvents.ResultsImportedDeleted, self.updateFilterRanges)
        self.app.eventManager.registerListener(RaccoonEvents.ResultsImportedDeleted, self.startFilter)


    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'filter.png'
        self._ICON_filter = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'run.png'
        self._ICON_run = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'floppy.png'
        self._ICON_save = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'removex.png'
        self._ICON_remove = ImageTk.PhotoImage(Image.open(f))


    def makeInterface(self):
        """ do the actual widget placement"""
        i = self.interior()

        """ NOT YET FUNCTIONAL IN BETA
        # toolbar
        f = tk.Frame(i)
        # filter set menu
        self.filterSetMenu = OptionMenuFix(f, labelpos= 'w', label_text = 'Filter set',
                label_font = self.FONT, menubutton_width = 40, menubutton_font = self.FONT, 
                menu_font = self.FONT, items = sorted(self.filterSets.keys()) )
        self.filterSetMenu.pack(side='left', anchor='w')
        # save button
        tk.Button(f, image=self._ICON_save, command=self.saveFilterSet,
            **self.BORDER).pack(side='left', anchor='w')
        # del button
        tk.Button(f, image=self._ICON_remove, command=self.saveFilterSet, 
            **self.BORDER).pack(side='left', anchor='w', padx=1)
        f.pack(expand=1,fill='x', padx=5)
        """
        self.autoupdate = tk.BooleanVar(value=False)

        # energy filter
        fp = FilterPropertyWidget(i, 'Energy', update_cb = self.autoFilter)
        #fp.setrange(-3.15, -12.10)
        fp.pack(side='top', anchor='w', padx=5, expand=1, fill='x')
        self.filtWidgets['energy'] = fp

        # ligand efficiency
        fp = FilterPropertyWidget(i, 'Ligand efficiency', update_cb = self.autoFilter)
        #fp.setrange(-0.10, -0.45)
        fp.pack(side='top', anchor='w', padx=5,pady=5, expand=1, fill='x')
        self.filtWidgets['leff'] = fp

        if self.mode == 'autodock':
            # clustering
            fp = FilterPropertyWidget(i, 'Cluster size', update_cb = self.autoFilter)
            #fp.setrange(-0.10, -0.45)
            fp.pack(side='top', anchor='w', padx=3, expand=1, fill='x')
            self.filtWidgets['clustering'] = fp

        # XXX interactions go here
        #self.interactionFilters = []
        self.interactFiltManager = RaccoonFilterInteract.InteractFiltManager(i, update_cb = self.autoFilter)
        self.interactFiltManager.pack(side='top', anchor='w', padx=5, expand=1, fill='both')
        #
        f = tk.Frame(i)
        self.applyButton = tk.Button(f, text='Apply filters', image = self._ICON_filter, 
                font = self.FONTbold, compound='left', command=self.startFilter, **self.BORDER)
        self.applyButton.pack(side='right', anchor='w', padx=1,expand=1,fill='x',pady=6)

        tk.Checkbutton(f, text='Auto-update', height=22, width=22, image=self._ICON_run, 
                compound = None, variable=self.autoupdate, onvalue=True, offvalue=False, 
                indicatoron=False, command=self.autoFilter, #offrelief='flat',
                **self.BORDER).pack(side='right', anchor='e', padx=1)

        f.pack(expand=1,fill='x', anchor='s', side='bottom', padx=5)

        f = tk.Frame(i) #, bg='white', **self.BORDER)
        tk.Label(f, text='Accepted ligands:', font=self.FONTbold, 
            anchor='w').pack(expand=0, fill='x',side='left', anchor='w')

        self.totalLabel = tk.Label(f, text=str(self._accepted), 
            font=self.FONT, anchor='w') #, bg='white', **self.BORDER)
        self.totalLabel.pack(expand=1, fill='x',side='left', anchor='w')
        # tk.Label(f, text='max accepted results')
        f.pack(expand=1,fill='x',anchor='s', side='bottom', padx= 6, pady=6)

    def buildInteractionPanel(self, parent):
        """ create the widget container """
        pass

    def updateFilterRanges(self, event=None):
        """ update the slider ranges when result properties change"""
        #print "UPDATE CALLED"
        prop = self.app.results_properties
        erange = prop['energy']
        leffrange = prop['leff']
        #print "UPDATE ENERGY", erange
        self.filtWidgets['energy'].setrange(*erange)
        #print "UPDATE LEFF", leffrange
        self.filtWidgets['leff'].setrange(*leffrange)

    def getfilters(self, _type = None):
        """ return the min/max tuples of all 
            filters or of the specified one
        """
        filters = {}
        if not _type == None:
            fpool = [_type]
        else:
            fpool = self.filtWidgets.keys()
        for f in fpool:
            filters[f] = self.filtWidgets[f].getvalues()
        return filters


    def selFilterSet(self, event=None):
        """ triggered when a filter set is selected """
        # check the auto/noauto?
        sel = self.filterSetMenu.getvalue()
        if sel == self._DEFAULT_FILTERSET:
            for n, f in self.filtWidgets.items():
                f.reset()
        if self.autostart.get():
            self.startFilter()

    def filterIssue(self, _type):
        """ warn the user to fix wrong filter values"""
        t = 'Filter error'
        i = 'warning'
        m = ('The value of the %s filter are not correct!' % _type)
        tmb.showinfo(parent=self.parent, message=m, icon=i)
        return

    def autoFilter(self, event=None):
        """ manage the trigger of autoupdate"""
        if not self.autoupdate.get(): 
            return
        if self._pending:
            self.parent.after_cancel(self._pending)
        self._pending = self.parent.after(500, self.startFilter)

    def startFilter(self, event=None):
        """ initiate the filtering process with GUI"""
        # XXX split this function in ACTION and UPDATE
        if self._pending: self._pending = None
        total_results = self.app.countResults()
        if self.app.results == {}:
            return
        settings = {}
        # gather properties filter settings
        e = self.filtWidgets['energy'].getvalues()
        if not e:
            self.filterIssue('energy')
            return
        settings['energy'] = {'values': e}
        le = self.filtWidgets['leff'].getvalues()
        if not le:
            self.filterIssue['ligand efficiency']
            return
        settings['leff'] = {'values' : le}
        # gather interaction filter settings
        settings['interactions'] = self.interactFiltManager.getvalues()
        self.app.setBusy()
        self.app.filterEngine.setFilters(settings)
        # open the gui
        fgui = FilterProgressGUI(self.parent, self.app)
        result = fgui.result
        self.app.setReady()
        if not result:
            return
        # update the status
        ecount = len(result['energy'])
        lecount = len(result['leff'])
        intcount = len(result['interactions'])
        accepted = len(result['total'])
        # e
        pc = hf.percent(ecount, total_results)
        self.filtWidgets['energy'].setpassed(ecount, pc)
        # le
        pc = hf.percent(lecount, total_results)
        self.filtWidgets['leff'].setpassed(lecount, pc)
        # interactions
        pc = hf.percent(intcount, total_results)
        #self.filtWidgets['interactions'].setpassed(lecount, pc)
        self.interactFiltManager.setpassed(intcount, pc)
        #  
        self._accepted = accepted
        text = '%d / %d\t [ %2.3f%% ]' % (self._accepted, 
                    total_results, hf.percent(self._accepted, total_results) )
        self.totalLabel.configure(text=text) # = str(self._accepted) )
        

    def saveFilterSet(self, event=None):
        """ ask for a new filter set name
            suggesting the initial one and 
            and checking for duplicates
        """
        self._DEFAULT_FILTERSET = '<default>'
        # walk over all filter widgets and ask for their settings
        settings = {}
        for f_name, f_obj in self.filtWidgets.items():
            settings[f_name] = f_obj.getvalues()
        #print "DEB> filter settings\n"
        #print settings

    def delfilterSet(self, event=None):
        """ remove a set from the filter set"""
        sel = self.filterSetMenu.getvalue()
        if sel == self._DEFAULT_FILTERSET:
            #print "[ filter saving default, nothing to do]"
            return
        t = 'Removing filter set'
        i = 'warning'
        m = ('Are you sure you want to remove the '
            'following filter set:\n\n%s') % sel
        if not tmb.askyesno(parent = self.frame,  title=t, message=m, icon=i):
            return
        self.filterSets.pop(sel)



class FilterProgressGUI(rb.RaccoonDefaultWidget, Pmw.Dialog):
    """ this widget shows the process of filtering """
    def __init__(self, parent, app):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        Pmw.Dialog.__init__(self, parent, buttons = ('Stop',),
            defaultbutton='Stop', title = 'Filtering...',
            command=self.stop, master=self.parent)
        self.app = app
        self.result = False
        self.total = self.app.countResults()
        self.pc_var = tk.DoubleVar(value=0.)
        f = tk.Frame(self.interior())
        self.progress = hf.ProgressBar(f, self.pc_var, w=300)
        self.progress.pack(expand=1, fill='x', anchor='n', side='top', padx=9, pady=3)
        f.pack(expand=0, fill='none', padx=10, pady=10)
        self.interior().after(100, self.start)
        self.activate() #geometry='centerscreenalways')

    def start(self, event=None):
        """ process """
        self.result = self.app.filterEngine.doFilter(cb=self.update)
        self.close()
        e = RaccoonEvents.FilterRunEvent()
        self.app.eventManager.dispatchEvent(e)

    def stop(self, event=None):
        """ halt ongoing filtering process"""
        self.app.filterEngine.STOP = True
        self.result = False

    def close(self, event=None):
        self.deactivate()

    def update(self, count, event=None):
        """ update progress bar """
        p = hf.percent(count, self.total)
        self.pc_var.set(p)
        self.progress.update()


class FilterPropertyWidget(rb.RaccoonDefaultWidget,Pmw.Group):
    """ widget to define properties filter values"""

    def __init__(self, parent, title, vmin=0, vmax=100, return_cb=None, update_cb=None):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        Pmw.Group.__init__(self, self.parent, tag_text = title, tag_font=self.FONTbold,
        #)
            ring_border=1, ring_highlightcolor='black', ring_highlightbackground='black',
            ring_highlightthickness=1,ring_relief='flat')
        
        self.title = title
        self.vmin = vmin
        self.vmax = vmax
        self.return_cb = return_cb
        self.update_cb = update_cb

        self.initIcons()
        self.makeInterface()

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))



    def makeInterface(self):
        """ do the widget stuff"""
        # radius of filter pie
        r_pie = 50
        self.lframe = tk.Frame(self.interior())
        self.lframe.pack(expand=0,fill=None, anchor='w', side='left')

        self.rframe = tk.Frame(self.interior())
        self.rframe.pack(expand=0,fill=None, anchor='e', side='left')

        # slider 
        f = tk.Frame(self.lframe)
        self.slider = RangeSlider(f, width=280, height=17, cb=self.slider_cb)
        #self.slider.canvas.bind('<Double-Button-2>', self.reset)
        self.slider.pack(anchor='w', side='left')
        f.pack(expand=0, fill='none',anchor='n', side='top')

        # entry text with validator
        entry_settings = { 'entry_width' : 10, 'entry_bd' : 1, 'entry_highlightbackground' :'black', 
                           'entry_borderwidth' : 1, 'entry_highlightcolor' :'black',
                           'entry_highlightthickness' : 1, 'entry_font' : self.FONT,
                           'entry_justify' : 'center',
                           'labelpos' : 'w', 'label_font': self.FONT,
                           'label_anchor' : 'e', 'label_width': 8,
                           }

        f = tk.Frame(self.lframe)
        # min 
        self.minentry = Pmw.EntryField(f, label_text = 'worst ', value=self.vmin, 
                validate = {'validator' : self.validatemin, 'minstrict': 0},
                command=self.setminslider, **entry_settings)
        self.minentry.pack(side='left', anchor='w',pady=4)

        # max
        self.maxentry = Pmw.EntryField(f, label_text = 'best ', value=self.vmax, 
            validate = {'validator' : self.validatemax, 'minstrict': 0},
            command=self.setmaxslider, **entry_settings)
        self.maxentry.pack(side='left', anchor='e',pady=4)

        # default button
        b = tk.Button(f, text='D', image=self._ICON_default, 
            command=self.reset, **self.BORDER)
        b.pack(side='left', anchor='e',pady=4, padx= 10)
        f.pack(side='top', anchor='w',padx=3, expand=1, fill='x')

        # pie
        self.pie = hf.PercentPie(self.rframe, radius=r_pie)
        self.pie.pack(anchor='n', side='top', padx=5, pady=5)
        #self.pie.set_percent(20)

        # passed label
        f = tk.Frame(self.rframe)
        tk.Label(f, text='passed :', font=self.FONTbold).pack(side='left',anchor='w')
        self.statusLabel = tk.Label(f, text='0', width=8, anchor='w', font=self.FONT)
        self.statusLabel.pack(side='left', anchor='w')
        f.pack(anchor='n', side='top')
        if not self.return_cb == None:
            self.bind('Return', self.return_cb)
            
    def reset(self, event=None):
        """ reset the filter to its defaults"""
        self.minentry.setvalue(self.vmin)
        self.maxentry.setvalue(self.vmax)
        self.slider.reset()
        if self.update_cb: self.update_cb()

    def getvalues(self):
        """ return the range values defined by
            this filter
        """
        if not self.minentry.valid():
            return False
        if not self.maxentry.valid():
            return False
        return sorted( (float(self.maxentry.getvalue()), float(self.minentry.getvalue())) )

    def setpassed(self, count, percentage):
        """ set the numerical value of 
            items that passed this filter
        """
        self.statusLabel.configure(text=count)
        self.pie.set_percent(percentage)

    def setrange(self, vmin=None, vmax=None):
        """ allows to redefine the max and min range values of this widget"""
        self.vmin = vmin
        self.vmax = vmax
        self.minentry.setvalue(self.vmin)
        self.maxentry.setvalue(self.vmax)
        self.slider.setrange(vmin, vmax)
        self.minentry.checkentry()
        self.maxentry.checkentry()


    def setminslider(self): #, value):
        """ update the slider with the min entry value"""
        #print "RECEIVED MINVALUE", self.minentry.getvalue()
        if self.minentry.valid():
            #print "Setting slider min"
            if not self.return_cb == None:
                self.return_cb()
            return
        #print "INVALID VALUE MIN"

    def setmaxslider(self): #, value):
        """ update the slider with the max entry value"""
        #print "RECEIVED MAXVALUE", self.maxentry.getvalue()
        if self.minentry.valid():
            #print "Setting slider max"
            if not self.return_cb == None:
                self.return_cb()
            return
        #print "INVALID VALUE MIN"

    def slider_cb(self, vmin, vmax):
        """ update the entries with the slider cb"""
        self.minentry.setvalue(vmin)
        self.maxentry.setvalue(vmax)
        if self.update_cb:
            self.update_cb()


    def updatevalues(self, event=None):
        """ syncronize the values between the slider
            and the entries
        """
        pass


    def validateEntry(self, value):
        """ checks that the entry is within the max/min range"""
        tkfloatcorrection  = 0.001
        vrange = sorted([self.vmin, self.vmax])
        if value == '' or value == '-':
            return Pmw.PARTIAL
        try:
            value = float(value)
        except:
            return Pmw.ERROR
        if value < vrange[0] - tkfloatcorrection:
            #print "too small %2.6f %2.6f (%2.6f)"%( value, vrange[0], vrange[0] + tkfloatcorrection)
            return Pmw.PARTIAL
        if value > vrange[1] + tkfloatcorrection:
            #print "too big %2.6f %2.6f"%( value, vrange[1])
            return Pmw.PARTIAL
        return Pmw.OK

    def validatemin(self, value):
        """ validate min entry value"""
        r = self.validateEntry(value)
        if not r == Pmw.OK:
            #print "MIN mainfail:", value, sorted([self.vmin, self.vmax])
            return r
        #try:
        value = float(value)
        if hasattr(self, 'maxentry'):
            maxentry = float(self.maxentry.getvalue())
            if self.vmin < self.vmax:
                if value <= maxentry:
                    #print "MIN mainok 2a:", value, "<=", maxentry, value <= maxentry
                    return Pmw.OK
                #print "MIN mainfail 2a:", value, "<=", maxentry, value <= maxentry
            elif self.vmin > self.vmax:
                if value >= maxentry:
                    #print "MIN mainok 2a:", value, ">=", maxentry, value <= maxentry
                    return Pmw.OK
                #print "MIN mainfail 2b:", value, ">=", maxentry,":", value >= maxentry
            return Pmw.PARTIAL
        else:
            return Pmw.OK
                
        #except AttributeError:
        #    # first time packing
        #    print "Packing sliders with initial values (catching error: %s)"%  sys.exc_info()[1]
        #    return Pmw.OK


    def validatemax(self, value):
        """ validate min entry value"""
        r = self.validateEntry(value)
        if not r == Pmw.OK:
            return r
        try:
            value = float(value)
            minentry = float(self.minentry.getvalue())
            if self.vmin < self.vmax:
                if value >= minentry:
                    return Pmw.OK
            elif self.vmin > self.vmax:
                if value <= minentry:
                    return Pmw.OK
                #print "MAXERROR2 v[%2.2f] <= min[%2.2f]" % ( value, minentry)
            return Pmw.PARTIAL
        except AttributeError:
            # first time packing
            return Pmw.OK



class FilterInteractionWidget(rb.RaccoonDefaultWidget,Pmw.Group):
    """ widget to define interaction filter settings"""

    def __init__(self, parent):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        Pmw.Group.__init__(self, self.parent, tag_text = 'Interactions', tag_font=self.FONTbold)
        
        self.initIcons()
        self.makeInterface()

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))



    def makeInterface(self):
        """ do the widget stuff"""
        tk.Label(self.interior(), text='INTERCTION 1  hydrogenbond', font = self.FONT).pack(expand=1, fill='x')
        tk.Label(self.interior(), text='INTERCTION 2  hydrogenbond', font = self.FONT).pack(expand=1, fill='x')
        tk.Label(self.interior(), text='INTERCTION 3  hydrogenbond', font = self.FONT).pack(expand=1, fill='x')

    def getvalues(self):
        """ this should return something interesting to be used for filetring"""
        return None




############################## VIEWER TAB

class ViewerTab(rb.TabBase, rb.RaccoonDefaultWidget):
    
    def __init__(self, app, parent, debug=False):
        rb.TabBase.__init__(self, app, parent, debug = False)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.resource = self.app.resource
        self.dockengine = self.app.dockengine
        self.camera = None
        #self.app.eventManager.registerListener(RaccoonEvents.SetResourceEvent, self.handleResource)
        self.eventManager = RaccoonEvents.RaccoonEventManager()
 
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

        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))

    def makeInterface(self):
        #tk.Label(self.frame, text="TERRIBLE THINGS ARE GOING TO HAPPEN HERE\n\n(VISUAL ANALYSIS)").pack(expand=1, fill='both')
        self.frame.pack(expand=1, fill='both')

        self.analysis_pad = Pmw.PanedWidget(self.frame, orient='horizontal', handlesize=-1,
            separatorthickness=10, separatorrelief='raised', )

        self.left = self.analysis_pad.add('info', min=0, size=300)
        self.right =  self.analysis_pad.add('viewer', min=3, size=600)
        handle = self.analysis_pad.component('handle-1')
        sep = self.analysis_pad.component('separator-1')        

        handle.place_forget()
        handle.forget()
        handle.pack_forget()
        handle.grid_forget()
        sep.configure(bd =2, highlightthickness=1, highlightbackground='black', highlightcolor='black')
        # nail handle
        tk.Frame(sep,height=40,width=4,bg='#fffeee',relief='sunken',bd=1,highlightbackground='black',
            highlightthickness=1).pack( anchor='center', padx=2,pady=2,side='left',expand=0,fill=None)
        self.analysis_pad.pack(expand=1,fill='both')

        # info pane
        #self.info_group = Pmw.Group(self.left, tag_text = 'Info', tag_font=self.FONTbold)

        # ligand info
        self.liginfopanel = LigInfoPanel(parent=self.left, app=self.app, viewertab=self)
        self.liginfopanel.pack(side='top', anchor='n', expand=0, fill='x', padx=3, pady=3)

        # results selector
        self.resSelector = ResultSelectorPanel(self.left, self.app, viewertab=self)
        self.resSelector.pack(side='top', anchor='n', expand=1, fill='both', padx=3, pady=3)

        #tk.Label(self.info_group.interior(), 
        #    text="TERRIBLE THINGS ARE GOING TO HAPPEN HERE\n\n(VISUAL ANALYSIS)").pack(expand=1, fill='both')
        tk.Frame(self.left, width=4).pack(side='right',anchor='w', expand=0,fill='y')
        #self.info_group.pack(expand=1,fill='both',side='left',anchor='w')
        # spacer
        tk.Frame(self.right, width=6).pack(side='left',anchor='w', expand=0,fill='y')

        # viewer pane
        self.viewer = ResViewer3D(parent=self.right, app=self.app, viewertab=self)
        self.viewer.pack(expand=1,fill='both',side='left',anchor='e')

        #self._makeviewer(self.viewer_group.interior())



class ResViewer3D(rb.RaccoonDefaultWidget,Pmw.Group):
    """ widget to define interaction filter settings"""
    def __init__(self, parent, app, viewertab):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        Pmw.Group.__init__(self, self.parent, tag_text = '3D Viewer', tag_font=self.FONTbold)
        #tk.Frame.__init__(self, self.parent)
        self.app = app 
        self.viewertab = viewertab
        self.camera = None
        self.initIcons()
        self.makeInterface()
        self.viewertab.eventManager.registerListener(RaccoonEvents.LigandResultPicked, self.loadResult)
        self.app.eventManager.registerListener(RaccoonEvents.FilterRunEvent, self.nuke)
        self.app.eventManager.registerListener(RaccoonEvents.ResultsImportedDeleted, self.nuke)

        self._currRec = {}
        self._currLig = []

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'center_lig.png'
        self._ICON_center_lig = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'center_rec.png'
        self._ICON_center_rec = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'center_all.png'
        self._ICON_center_all = ImageTk.PhotoImage(Image.open(f))


    def makeInterface(self):
        """ create the analysis camera and its toolbar"""
        t = tk.Frame(self.interior())
        # center ligand
        cb = CallbackFunction(self.centerView, 'lig')
        tk.Button(t, text='S', image=self._ICON_center_lig, compound=None, command=cb, **self.BORDER).pack(side='top', anchor='n')

        #center receptor
        cb = CallbackFunction(self.centerView, 'rec')
        tk.Button(t, text='s', image=self._ICON_center_rec, compound=None, command=cb, **self.BORDER).pack(side='top', anchor='n',pady=1)

        # center all
        cb = CallbackFunction(self.centerView, None)
        tk.Button(t, text='I', image=self._ICON_center_all, compound=None, command=cb, **self.BORDER).pack(side='top', anchor='n')
        t.pack(side='left', anchor='n', expand=0, fill='x')

        # grid cam name 
        name = 'analysiscam'
        bgcolor = (.2, .2, .2,)

        if self.app.viewer == None:
            # XXX reinitialize fonts?
            self.app.viewer = RaccoonPmvCamera.EmbeddedMolViewer()
            self.app.molviewer = self.app.viewer.mv
            self.app.parent.bind_all('<F12>', self.app.viewer.togglepmv)
        # adding config camera
        if self.camera == None:
            self.camera = self.app.viewer.addCamera(self.interior(), name=name, depth=True, bgcolor=bgcolor)
            self.camera_name = self.viewertab.camera_name = name
        # self.viewertab.eventManager.registerListener(RaccoonEvents.LigandResultPicked, 

    def loadResult(self, event=None):
        """ manage loading the molecules in results
            lig + rec
        """
        ligname = event.ligname
        jobname = event.jobname
        pose = event.pose
        liginfo = self.app.results[jobname]['results'][ligname]['data'][pose]
        path = self.app.results[jobname]['path']
        recname = liginfo['recname']
        ligfname = liginfo['pdbqt']
        # load receptor
        self.loadCheckRec(recname, path, jobname)
        # load ligand
        self.loadCheckLig(ligname, ligfname)
        # load interactions


    def loadCheckRec(self, recname, path, jobname):
        """ check if receptor to be loaded is already present in the session
            if not, load it
        """

        recfname = self.app.results[jobname]['rec']
        #print "LOADING RECFNAME", recfname
        cam = self.camera_name
        viewer = self.app.viewer
        if not self._currRec == {}:
            if self._currRec['name'] == recname:
                return
            else:
                viewer.deleteInCamera( self._currRec['obj'], cam)
                self._currRec['name'] = recname
        
        # FIXME fragile! this shouldn't be used unless desperate measures
        if recfname == None:
            print "WARNING! GUESSING RECEPTOR FILENAME"
            recfname = "%s%s%s%s" % (path, os.sep, recname, '.pdbqt')

###        if not os.path.isfile(recfname):
###            try:
###                self.app.results # get the recfname from the logfile imported
###
###            except:
###                ask?
###
###
###            
###
        self._currRec = { 'name' : recname, 'fname' : recfname }
        self._currRec['obj'] = viewer.loadInCamera( recfname, cam)
        self.applyRecStyle()


    def loadCheckLig(self, ligname, ligfname):
        """ check if ligand to be loaded is already present in the session
            if not, load it
            if it is loaded but it is not the main, move it to first
            ( for applying style)

            1. if the mode is 'single' (only one visible), delete all but first ligand
            2. requested ligand is already the main one: RETURN
            3. requested ligand is not the main one: move to [0], apply style, RETURN
            4. requested ligand is not the main one: load it, move to [0]
        """
        cam = self.camera_name
        viewer = self.app.viewer
        # cleanup mode
        mode = 'single'
        if mode == 'single' and len(self._currLig)>1:
            # delete non-main 
            for i in range(len(self._currLig)-1):
                obj = self._currLig[i+1]['obj']
                viewer.deleteInCamera(obj,cam)
        
        for i in range(len(self._currLig)):
            lig = self._currLig[i]
            if (lig['name'] == ligname) and (lig['fname'] == ligfname):
                if i == 0:
                    # already loaded and main
                    return
                else:
                    # already loaded but not main
                    self._currLig = self._currLig[i] + self._currLig[:i] + self._currLig[i+1:]
                    # apply STYLES (main, secondary)
                    # print "RESORT CALL"
                    self.applyLigStyle()
                    return
        # the main was not accepted
        if mode == 'single' and len(self._currLig) > 0:
            obj = self._currLig[0]['obj']
            viewer.deleteInCamera(obj, cam)
            self._currLig = []
        newlig = { 'name' : ligname, 'fname' : ligfname }
        newlig['obj'] = viewer.loadInCamera(ligfname, cam)
        self._currLig = [newlig] + self._currLig
        #print "FINAL CALL"
        self.applyLigStyle()


    def applyLigStyle(self, event=None):
        """ apply the representations specific for the ligands:

            main:       the principal ligand
            secondary:  multiple ligands visible
        
        """
        viewer = self.app.viewer
        #representations  = {
        #style = { 'repr' : 'stick' }

        main = self._currLig[0]['obj']
        viewer.mv.displaySticksAndBalls(main, log=0, cquality=0, sticksBallsLicorice='Licorice', 
                    bquality=0, cradius=0.2, setScale=True, only=False, bRad=0.3, negate=False, 
                    bScale=0.0, redraw=True)
        carbons = [ "%s:::%s" % (main.name, x.name) for x in main.allAtoms if x.element == 'C']
        carbons = ";".join(carbons)
        viewer.mv.colorByAtomType(main.name,['balls', 'lines', 'sticks'], log=0)
        carbon_color = [[1.0, 0.5098039215686274, 0.25882352941176473]] # orange
        viewer.mv.color(carbons, carbon_color, ['balls', 'lines', 'sticks'], log=0)

        #if not main.geomContainer.geoms['sticks'].culling == 0:
        main.geomContainer.geoms['sticks'].applyStrokes()
        #if not mol.geomContainer.geoms['balls'].culling ==0:
        main.geomContainer.geoms['balls'].applyStrokes()

        
        if len(self._currLig)<2:
            return
        for m in self._currLig[1:]:
            viewer.mv.displayLines(m, negate=False, displayBO=False, lineWidth=2, log=0, only=True)

        


    def applyRecStyle(self, event=None):
        """ apply representation to receptor"""
        
        viewer = self.app.viewer

        carbon_color = [[0.5176470588235295, 1.0, 0.0]]  # soft green

        mol = self._currRec['obj']
    
        #carbons = [ "%s:%s:%s:%s" % (mol.name, x.parent.parent.name, x.parent.name, x.name) for x in mol.allAtoms if x.element == 'C']
        mol.geomContainer.geoms['lines'].protected=False
        for a in mol.allAtoms:
            if a.element == 'C':
                a.colors['lines'] = carbon_color[0]
        mol.geomContainer.geoms['lines'].Set(lineWidth=1)
        #mol.geomContainer.geoms['lines'].Set(visible=1, redo=1)
        viewer.mv.displayLines(mol, negate=False, displayBO=False, lineWidth=1, log=0, only=True)

        #carbons = ";".join(carbons)
        #carbons = "%s:::C*" % mol.name
        #print "CARBANZ", carbons
        #mol.geomContainer.geoms['lines'].Set(lineWidth=1)
        # FIXME very slow! ask michel
        #viewer.mv.color(carbons, carbon_color, ['lines'], log=0, redraw=0)


    def nuke(self, event=None):
        """ remove all currently loaded molecules
            (e.g. when right after a new filtering)
        """
        self.app.viewer.nukeCamMols(self.camera_name)
        self._currLig = []
        self._currRec = {}
        e = RaccoonEvents.LigandResultNuked()
        self.viewertab.eventManager.dispatchEvent(e)

    def centerView(self, target=None, event=None):
        """ center view in the 3D config viewer"""
        #root = self.app.viewer.rootObject
        #print 'TARGET', target
        if target == 'box': # MS FIXME .. there is not call back that passes target = 'box'
            #print "Center box"
            item = self.Box3D

        elif target == 'lig':
            if len(self._currLig):
                item = self._currLig[0]['obj'].geomContainer.masterGeom
            else:
                return
            
        elif target == 'rec':
            if len(self._currRec):
                item = self._currRec['obj'].geomContainer.masterGeom
            else:
                return
        else:
            item = None
        self.app.viewer.centerView(item)



class LigInfoPanel(rb.RaccoonDefaultWidget,Pmw.Group):
    """ widget to define interaction filter settings"""
    def __init__(self, parent, app, viewertab):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        Pmw.Group.__init__(self, self.parent, tag_text = 'Ligand properties', tag_font=self.FONTbold)
        #tk.Frame.__init__(self, self.parent)
        self.app = app 
        self.viewertab = viewertab
        self.initIcons()
        self.makeInterface()
        self.viewertab.eventManager.registerListener(RaccoonEvents.LigandResultPicked, self.updateTable)
        self.viewertab.eventManager.registerListener(RaccoonEvents.LigandResultNuked, self.initTable)

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))

    def makeInterface(self):
        """ do the widget stuff"""
        i = self.interior()
        f = tk.Frame(i)
        self.table = hf.SimpleTable(f, title_item='column', title_color = '#d8daf8',
                    cell_color = 'white', title_font = self.FONTbold, cell_font = self.FONT,
                    autowidth=True)
        # spacer
        f.pack(side='top',anchor='w', expand=1,fill='both', padx=10, pady=10)
        #tk.Label(f, text='   ').pack(side='top')
        self.initTable()

    def initTable(self, event=None):
        """ initialize the table with empty values"""
        e = '       '
        fields = [ 'Name', 'Receptor', 'Energy', 'Lig.efficiency']
        data = [ [f, e] for f in fields ]
        self.table.setData(data)

    def updateTable(self, event=None):
        """ update table with the current ligand info """
        ligname = event.ligname
        jobname = event.jobname
        pose = event.pose
        liginfo = self.app.results[jobname]['results'][ligname]['data'][pose]
        data = [ [ 'Name',  ligname],
                 [ 'Receptor', liginfo['recname'] ],
                 [ 'Energy', liginfo['energy'] ],
                [ 'Lig.efficiency', liginfo['leff'] ],
                ]
        self.table.setData(data)


class ResultSelectorPanel(rb.RaccoonDefaultWidget,Pmw.Group):
    """ widget to define interaction filter settings"""
    def __init__(self, parent, app, viewertab):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        Pmw.Group.__init__(self, self.parent, tag_text = 'Results', tag_font=self.FONTbold)
        self.app = app 
        self.viewertab = viewertab
        self.initIcons()
        self.makeInterface()
        self.app.eventManager.registerListener(RaccoonEvents.FilterRunEvent, self.updateResPanel)
        self.app.eventManager.registerListener(RaccoonEvents.ResultsImportedDeleted, self.updateResPanel)

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))
        f = icon_path + os.sep + 'select_all.png'
        self._ICON_selall = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'invert_selection.png'
        self._ICON_selinvert = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'deselect.png'
        self._ICON_seldel = ImageTk.PhotoImage(Image.open(f))

    def makeInterface(self):
        """ do the widget stuff"""
        i = self.interior()
        # 
        t = tk.Frame(i)
        tk.Button(t, text='A', image=self._ICON_selall, command=self.selectAll, **self.BORDER).pack(side='left', anchor='w', padx=0)
        tk.Button(t, text='D', image=self._ICON_seldel, command=self.selectNone, **self.BORDER).pack(side='left', anchor='w', padx=1)
        tk.Button(t, text='I', image=self._ICON_selinvert, command=self.selectInvert, **self.BORDER).pack(side='left', anchor='w',padx=0)
        t.pack(expand=0,fill='x',padx=6)

        #
        self.makeListbox()
        self.updateResPanel()


    def makeListbox(self):
        """ create and setup the listbox widget"""
        i = self.interior()
        cols = ('sel', 'rank', 'ligand', 'receptor', 'energy',
            'l.eff.', 'poses', 'job', 'filename')
        self.respanel = TkTreectrl.ScrolledMultiListbox( i, bd=2)
        self.respanel.listbox.config(bg='white', fg='black', font=self.FONT,
            columns = cols)
        self.respanel.pack(expand=1, fill='both', anchor='n', padx='4')

        lbox = self.respanel.listbox
        lbox.state_define('Checked')
        lbox.icons = {}
        
        checkedIcon = lbox.icons['checkedIcon'] = \
            tk.PhotoImage(master=lbox, 
            data=('R0lGODlhDQANABEAACwAAAAADQANAIEAAAB/f3/f39',
                   '////8CJ4yPNgHtLxYYtNbIbJ146jZ0gzeCIuhQ53N',
                   'JVNpmryZqsYDnemT3BQA7'))
        unCheckedIcon = lbox.icons['unCheckedIcon'] = \
            tk.PhotoImage(master=lbox, 
            data=('R0lGODlhDQANABEAACwAAAAADQANAI',
            'EAAAB/f3/f39////8CIYyPNgHtLxYYtNbIrMZTX+l9WThwZAmSppqGmADHcnRaBQA7'))

        el_image = lbox.element_create(type='image', image=(
            checkedIcon, 'Checked', unCheckedIcon, ()))
        styleCheckbox = lbox.style_create()
        lbox.style_elements(styleCheckbox, lbox.element('select'), el_image, lbox.element('text'))

        lbox.style_layout(styleCheckbox, el_image, padx=9, pady=2)
        lbox.style(lbox.column(0), styleCheckbox)
        colors = ('white', '#ddeeff')
        for col in range(8):
            lbox.column_configure(lbox.column(col), itembackground=colors)
        lbox.bind('<ButtonRelease-1>', self.leftClick)
        lbox['selectbackground'] = 'white'
        lbox['selectforeground'] = 'black'


    def selectAll(self, event=None, negate=False, invert=False):
        """ select all filtered ligands"""
        lbox = self.respanel.listbox
        checkmark = { True: 'Checked', False:'!Checked'}
        for i in range(lbox.size()):
            item = lbox.get(i)[0]
            ligname = item[2].strip()
            jobname = item[7].strip()
            if negate:
                status = False
            elif invert:
                status = not self.app.results[jobname]['results'][ligname]['selected']
            else:
                status = True
            self.app.results[jobname]['results'][ligname]['selected'] = status
            lbox.itemstate_forcolumn(i+1, 0, checkmark[status])
            # generate selection EVENT here

    def selectNone(self, event=None):
        """ deselect all filtered ligands """
        self.selectAll(negate=True)

    def selectInvert(self, event=None):
        """ invert current selection """
        self.selectAll(invert=True)


    def updateResPanel(self, event=None):
        """ add/remove items to the respanel"""
        #print "RESULT PANEL UPDATED"
        check_state = {True: 'Checked', False : '!Checked'}
        lbox = self.respanel.listbox
        lbox.delete(0,'end')
        accepted = self.app.acceptedResults()
        if not len(accepted):
            return
        t = "   %s   "
        f = "   %2.3f  "
        for i in range(len(accepted)):
            d = accepted[i]
            sel = check_state[d['selected']]
            lbox.insert('end', '', t % (i+1), t % d['name'], t % d['recname'],
                               f % d['energy'], f % d['leff'], t % d['poses'], 
                               t % d['job'], t % d['filename'])
            lbox.itemstate_forcolumn('end', 0, sel)
        lbox.see(0)

    def leftClick(self, event=None):
        """ manages left clicks on the box"""
        lbox = self.respanel.listbox
        lbox.unbind('<ButtonRelease-1>')
        self.app.setBusy()
        try:
            sel = lbox.curselection()
            identify = lbox.identify(event.x, event.y)
            item = None
            if identify:
                try:
                    item, column, element = identify[1], identify[3], identify[5]
                except IndexError:
                    return
            if item == None: return
            lbox['selectbackground'] = '#ffff00'
            values =  lbox.get(lbox.index(item=item))[0]
            ligname = values[2].strip()
            jobname = values[7].strip()
            lbox.select_anchor(lbox.index(item=item))
            if int(column) == 0:
                lbox.itemstate_forcolumn(item, column, '~Checked')
                self.app.results[jobname]['results'][ligname]['selected'] = not self.app.results[jobname]['results'][ligname]['selected']
                lbox.update_idletasks()
        except IndexError:
            print "IndexError catched"
            self.app.setReady()
            return
        finally:
            try:
                lbox.select_clear()
                lbox.select_set(*sel)
                e = RaccoonEvents.LigandResultPicked(ligname=ligname, jobname=jobname, pose=0)
                self.viewertab.eventManager.dispatchEvent(e)
            except:
                #print "*" * 10, "\nERR", sys.exc_info()[1],"\n", "*"*10
                pass
            lbox.bind('<ButtonRelease-1>', self.leftClick)
            self.app.setReady()


class ExportTab(rb.TabBase, rb.RaccoonDefaultWidget):
    
    def __init__(self, app, parent, debug=False):
        rb.TabBase.__init__(self, app, parent, debug = False)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        
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

        f = icon_path + os.sep + 'csv.png'
        self._ICON_csv = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'open.png'
        self._ICON_open = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))

    def makeInterface(self):

        
        group = Pmw.Group(self.frame, tag_text='Results',tag_font=self.FONTbold)
        parent = group.interior()

        # sel level  ################################33
        self.selectLevel = tk.IntVar(value=0) # 0: selected, 1: filtered, 2: all

        # selected
        self.selButton = tk.Radiobutton(parent, text='Selected', variable=self.selectLevel, indicatoron=1, anchor='w',
            value=0, width=7, font=self.FONT)
        self.selButton.pack(expand=0, fill='none',side='left',anchor='w',pady=5, padx=5)
        # filtered
        self.filtButton = tk.Radiobutton(parent, text='Filtered', variable=self.selectLevel, indicatoron=1, anchor='w',
            value=1, width=7, font=self.FONT)
        self.filtButton.pack(expand=0, fill='none',side='left',anchor='w',pady=5, padx=5)
        # all
        self.allButton = tk.Radiobutton(parent, text='All', variable=self.selectLevel, indicatoron=1, anchor='w',
            value=2, width=7, font=self.FONT)
        self.allButton.pack(expand=0, fill='none',side='left',anchor='w',pady=5, padx=5)

        group.pack(expand=0, fill='none',padx=3, anchor='w', side='top')

        f = tk.Frame(self.frame)
        # buttons        
        #tk.Button(parent, text='Save log data...', compound='left', image=self._ICON_open, #anchor ='w',
        #    justify='center', command=self.saveLog).grid(row=3,column=0,sticky='we',padx=3,pady=3)
        f.pack(anchor='w', side='top', expand=0, pady=5)


        # STRUCTURES ##################################

        g = Pmw.Group(self.frame, tag_text = 'Structures', tag_font=self.FONTbold)
        f = tk.Frame(g.interior())
        self.structLig = tk.BooleanVar(value=True)
        self.structRec = tk.BooleanVar(value=True)
        self.structBox = tk.BooleanVar(value=True)

        tk.Checkbutton(f, text = 'Ligands', font=self.FONT, variable=self.structLig, onvalue=True, 
            width=22, offvalue=False, anchor='w').pack(side='top', anchor='w', padx=5, pady=5)
        tk.Checkbutton(f, text = 'Receptor', font=self.FONT, variable=self.structRec, onvalue=True, 
            width=22, offvalue=False, anchor='w').pack(side='top', anchor='w', padx=5, pady=5)
        #tk.Checkbutton(f, text = 'Box', font=self.FONT, variable=self.structBox, onvalue=True, 
        #    width=10, offvalue=False, anchor='w').pack(side='top', anchor='w', padx=5, pady=5)
        f.pack(side='left', anchor='w', padx=0)

        
        f = tk.Frame(g.interior())
        tk.Button(f, text = 'Save PDB...', width=110, font=self.FONT, command = self.savePdb, compound='left',
            anchor='w', image = self._ICON_open, **self.BORDER).pack(side='top', anchor='w',padx=3)
        tk.Button(f, text = 'Save PDBQT...', width=110, font=self.FONT, command = self.savePdbqt, compound='left',
            anchor='w', image = self._ICON_open, **self.BORDER).pack(side='top', anchor='w',padx=3,pady=1)
        f.pack(side='top', anchor='w', padx=10)

        g.pack(anchor='w', side='top', expand=0, pady=5,padx=3)

        g = Pmw.Group(self.frame, tag_text = 'Summary log', tag_font=self.FONTbold)
        tk.Label(g.interior(), text='CVS summary log file', width = 22, font=self.FONT).pack(side='left', anchor='w', padx=2)
        tk.Button(g.interior(), text = 'Save summary...', width=110, font=self.FONT, command = self.saveLog, 
            compound='left', anchor='w', image=self._ICON_csv, **self.BORDER).pack(side='top', anchor='w',padx=3,pady=3)

        g.pack(anchor='w', side='top', expand=0, pady=5,padx=3)

        self.frame.pack(expand=1, fill='both')

    def updateSelectButton(self, event=None):
        """ udpate count of selected ligands"""
        self.selButton

    def updateFilterButton(self, event=None):
        """ update the count of filtered ligands"""
        self.filtButton


    def updateAllbutton(self, event=None):
        """ update the count of all ligands"""
        self.allButton


    def getData(self):
        """ query the app for the required data set"""
        # self.selectLevel = tk.IntVar(value=0) # 0: selected, 1: filtered, 2: all
        sel = self.selectLevel.get()
        if sel == 0: # selected
            data =  self.app.selectedResults()
        elif sel == 1: # filtered
            data = self.app.acceptedResults()
        elif sel == 2: # all imported results
            data = self.app.acceptedResults(anything=True)
        if not len(data):
            t = 'No results available'
            i = 'info'
            m = ('There are no results available. Import new results or change filter settings.')
            tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
            return []
        return data

    def saveLog(self, event=None, sep=','):
        """ export text log file
            sep = ',' '\t'
        """
        data = self.getData()
        if not len(data):
            return
        buff = []
        t = 'Select log filename'
        ft = [('Comma separated values', '*.csv'), ("Any file type...", "*")] 
        idir = self.app._lastdir
        i = os.path.expanduser("~")
        fname = tfd.asksaveasfilename(parent=self.parent,
            title=t, filetypes=ft, initialdir=idir)
        if not fname: return
        fname = self._listfixer(fname)[0]
        if not fname[-4:].lower() == '.csv': fname = fname+'.csv'
        info = [ "%(name)s", "%(recname)s", "%(energy)2.3f", "%(leff)2.3f", "%(poses)d", "%(filename)s"]
        line = sep.join(info)
        for d in data:
            buff.append( line % d )
        try:
            hf.writeList(fname, buff, addNewLine=1)
            t = 'Log saved'
            i = 'info'
            m = ('The log file has been saved successfully')
            tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
        except:
            e = sys.exc_info()[0]
            t = 'Log saving error'
            i = 'error'
            m = ('An error occurred saving the log:\n\nfile: %s\n\nerror: %s') % (fname, e)
            tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)


    def savePdb(self, event=None):
        """ export ligands as PDB"""
        self.saveMols('pdb')

    def savePdbqt(self, event=None):
        """ export ligands as PDBQ"""
        self.saveMols('pdbqt')


    def saveMols(self, _format='pdb'):
        """ save molecules"""
        dolig = self.structLig.get()
        dorec = self.structRec.get()
        #dobox = self.structBox.get()

        self.structBox = tk.BooleanVar(value=True)
        data = self.getData()
        if not len(data):
            return
        t = 'Select the directory name to be created'
        i = self.app._lastdir
        i = os.path.expanduser("~")

        p = self.parent
        # xxx warn user if mols are more than 500?

        rdirname = tfd.askdirectory(parent=p, title=t, initialdir=i, mustexist=False)
        if not rdirname: return
        rdirname = self._listfixer(rdirname)[0]
        hf.makeDir(fullpath=rdirname)

        if dolig: 
           ldirname = rdirname + os.sep + 'ligands'
           hf.makeDir(fullpath=ldirname)

        receptors = []
        error = None
        currfile = None
        currdir = None
        try:
            for d in data:
                lfile = currfile = d['filename']
                currdir = ldirname
                job = d['job']

                if dolig:
                    if _format == 'pdb':
                        self.makePdb(lfile, ldirname)
                    elif _format == 'pdbqt':
                        self.makePdbqt(lfile, ldirname)
                if dorec:
                    currdir = rdirname
                    r = currfile = d['recname']
                    if not r in receptors: 
                        receptors.append(r)
                    recfile = self.app.results[job]['rec']
                    #recfile = os.path.join(recpath,r+'.pdbqt')
                    if _format == 'pdb':
                        self.makePdb(recfile, rdirname)
                    elif _format == 'pdbqt':
                        self.makePdbqt(recfile, rdirname)
                    #shutil.copy2(recfile, rdirname)
        except:
            error = sys.exc_info()[1]
            t = 'Results export'
            i = 'info'
            m = 'Result files exported successfully'
        if not error == None:
            i = 'error'
            m = ('An error occurred in the copy '
             'of the result files:\n\nError: %s'
             '\n\nDir name: "%s"\n\nFile name: "%s"') % ( error, currdir, currfile)
            tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)



    def makePdb(self, filename, destpath=None):
        """ convert the input file to PDBQT"""
        mol = Read(filename)[0]
        mol.buildBondsByDistance()
        mol.allAtoms.number = range(1, len(mol.allAtoms)+1)
        writer = PdbWriter()
        basename = os.path.basename(filename)
        outname = destpath + os.sep + os.path.splitext(basename)[0] + '.pdb'
        writer.write(outname, mol.allAtoms, records=['ATOM', 'HETATM'])

    def makePdbqt(self, filename, destpath=None):
        """ copy the PDBQT in the required dir"""
        shutil.copy2( filename, destpath)

