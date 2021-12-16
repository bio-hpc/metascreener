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
import RaccoonBasics as rb
import RaccoonEvents
import RaccoonServers
import RaccoonServices
import CADD.Raccoon2.HelperFunctionsN3P as hf
import DebugTools
import os, Pmw
from PmwOptionMenu import OptionMenu as OptionMenuFix
import Tkinter as tk
import TkTreectrl
import tkMessageBox as tmb
import tkFileDialog as tfd
from PIL import Image, ImageTk
# mgl modules
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction # as cb
import DebugTools

class ProcessResultsGui(rb.RaccoonDefaultWidget,Pmw.Dialog, DebugTools.DebugObj):
    """ widget for managing results generation and
        show progress

        the class can be used by specifying a known job to process:

            ProcessResultsGui(parent, app, job=[p,e,v], auto)

        and all data will be filled in automatically, or by specifying
        explicit ligand files list and logfile to generate.

            ProcessResultsGui(parent, app, ligands = [file1, file2...], logfile='rec_ligLibrary.log' )
    """
    def __init__(self, parent, app, ligands=None, receptor=None, logfile=None, job=None, auto=False, debug=False):
        """ """
        rb.RaccoonDefaultWidget.__init__(self, parent)
        DebugTools.DebugObj.__init__(self, debug)
        Pmw.Dialog.__init__(self, parent, buttons = ('Stop',),
            defaultbutton='Stop', title = 'Processing results',
            command=self.stop, master=self.parent)
        bbox = self.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)
        self.job = job
        self.app = app
        self.auto = auto
        self.problematic = []
        self._current = ('none', 'none', 'none')
        self.status = False
        if self.job:
            self.getData()
        else:
            self.ligands = ligands
            if receptor:
                self.receptor = receptor
            else:
                self.receptor = self.app.resultsProcessor.processor.recname
            self.logfile = logfile
            self.dirname = os.path.dirname(os.path.normpath(logfile))
            self.logfile = os.path.basename(os.path.normpath(logfile))

        # build GUI
        d = self.interior()
        f = tk.Frame(d)
        tk.Label(f, text='Processing: ', 
            font=self.FONTbold).pack(side='left', anchor='w', padx=9)
        self.label = tk.Label(f, text='', font=self.FONT, anchor='w')
        self.label.pack(side='left', anchor='w')
        f.pack(expand=0, fill='x',side='top', anchor='n',pady=5)
        x = tk.Frame(d)
        self.pc_var = tk.DoubleVar(value=0.)
        self.progress = hf.ProgressBar(x, self.pc_var, w=300)
        self.progress.pack(expand=1, fill='x',anchor='n', side='top',padx=9,pady=3)
        x.pack(expand=1, fill='x', anchor='n', side='top', pady=5)

        status = self.check()
        if status == True:
            self.STOP = False
            # if successful: import the generated logfile
            # the log file must be saved with the name of the directory? 
            # receptor Name?
            self.interior().after(100, self.start)
            self.activate()
        else:
            self.STOP = True
            self.problematic = [['None', status ]]
            self.label.configure(text='DONE')
            self.updateButton()

    def getData(self):
        """ retrieve from the history all info required
            to process results
        """
        p,e,v = self._current = self.job
        jobinfo = self.app.history[p][e][v]
        self.dirname = self.app.getJobDir( job=self.job )
        self.logfile = "%s%s%s_summary.log" % (self.dirname, os.sep, v) 
        self.ligands = self.searchLigands(self.dirname)
        # get receptor file from the job
        rec = self.dirname + os.sep + jobinfo['receptor'] # + '.pdbqt'
        if os.path.isfile(rec):
            self.receptor = rec
            self.app.resultsProcessor.setReceptor(self.receptor)
    
    def check(self):
        """ check requirements before starting process"""
        # check dir
        if not os.path.isdir(self.dirname):
            self.dprint("[%s|%s|%s] *CHECK FAIL* job dir [%s] not accessible." % (self._current+tuple(self.dirname)))
            return "Local VS directory inaccessible"
        # check ligands
        if not len(self.ligands.keys()):
            self.dprint("[%s|%s|%s] *CHECK FAIL* no ligands" % (self._current))
            return "No ligands found"
        # check receptor
        if self.receptor == None:
            self.dprint("[%s|%s|%s] *CHECK FAIL* receptor is not defined" % (self._current))
            return "Missing receptor"
        return True

    def callback(self, name, count):
        """ callback to be passed to the processor"""
        self.label.configure(text=name)
        tot = len(self.ligands.keys())
        self.pc_var.set( hf.percent(count, tot) )
        self.progress.update()

    def searchLigands(self, dirname, cb=None): #, pattern= '*_out.pdbqt'):
        """ scan dir for vina results"""
        
        pattern_list = { 'autodock' : '*.dlg',
                         'vina'     : '*_out.pdbqt',
                       }
        pattern = pattern_list[ self.app.getDockingEngine() ] 
        dockfiles = hf.pathToList(dirname, recursive = True, pattern = pattern)
        #self.dprint("found %s dockfiles" % dockfiles)
        result = {}
        for d in dockfiles:
            name = os.path.basename(d).split("_out.pdbqt")[0]
            result[name] = d
        return result

    def stop(self, event=None):
        """ """
        p = self.interior()
        t = 'Confirmation'
        i = 'warning'
        m = 'Stop the current download?'
        if not tmb.askyesno(parent=p,title=t, message=m, icon=i):
            return
        self.STOP = True
        self.updateButton()

    def close(self, event=None):
        """ destroy the widget"""
        self.deactivate(False)
        self.withdraw()

    def updateButton(self, auto=True, event=None):
        """ change the button Stop-> Close"""
        bbox = self.component('buttonbox') 
        i = bbox.index(Pmw.DEFAULT)
        b = bbox.button(i)
        b.configure(text='Close', command=self.close)
        self.configure(command=self.close)
        if len(self.problematic):
            t = 'Problematic files'
            i = 'warning'
            m = ('There have been %d errors'
                'while processing.\n\nInspect the '
                'list of error messages?') % len(self.problematic)
            if tmb.askyesno(parent=self.interior(), title=t, icon=i,message=m):
                ResultProblemsInspector(self.parent, self.app, self.problematic)
        print "RUNNING LATE"
        if auto:
            self.close()


    def asklogfile(self):
        """ ask the user for a logfilename"""
        t = 'Log filename'
        m = ('Enter the log file name where results summary will '
            'be written:')
        logfile = Pmw.PromptDialog(self.parent, title=t, label_text=m, label_font = self.FONT,
            master = self.parent,
            entryfield_labelpos = 'n', defaultbutton=0, buttons=('OK','Cancel'),
            entryfield_value = self.logfile,
            entryfield_validate = {'min':1, 'minstrict':0, 'validator': hf.validateFname})
        bbox = logfile.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)
        entry = logfile.component("entryfield")
        entry.component('entry').configure(font=self.FONT)
        result = logfile.activate()
        if result == 'Cancel':
            return False
        if not logfile.valid():
            return
        logfile = logfile.get()
        if not logfile[-4:] == '.log':
            logfile += '.log'
        self.logfile = os.path.join(self.dirname, logfile)
        return True

    def start(self, event=None):
        """ start the processing"""
        if not self.auto:
            if not self.asklogfile():
                self.close()
        tot = len(self.ligands)
        if tot == 0:
            self.dprint("***No ligands!***")
        c = 0
        self.app.resultsProcessor.ligands = self.ligands
        self.problematic = self.app.resultsProcessor.generateResults(logfile = self.logfile, 
                                                   cb = self.callback, 
                                                   stop=self.STOP)
        if os.path.exists(self.logfile) and self.job:
            p,e,v = self.job
            self.status = True
            self.app.updateJobHistory( name=v,
                prj=p, exp=e, properties = {'summary': self.logfile})
        self.label.configure(text='DONE')
        self.updateButton()


class ResultProblemsInspector(rb.RaccoonDefaultWidget, Pmw.Dialog):
    """ show problematic result files and error messages"""
    def __init__(self,parent, app, problematic):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        Pmw.Dialog.__init__(self, parent, title = 'Problematic results',
            buttons=('Export', 'Close'), defaultbutton='Close', command=self.click)
        self.app = app
        self.problematic = problematic
        cols = ('Ligand file', 'error')
        self.panel = TkTreectrl.ScrolledMultiListbox(self.interior(), bd=2)
        self.panel.listbox.config(bg='white', fg='black', font=self.FONT,
            columns = cols)
        self.panel.pack(expand=1, fill='both', anchor='n', padx='4')
        for f,e in self.problematic:
            self.panel.listbox.insert('END', f, e)
        self.activate()


    def click(self, event=None):
        """ dispatch the button events"""
        if event == 'Close':
            self.close()
        elif event == 'Export':
            self.export()


    def close(self, event=None):
        self.deactivate()
        
    def export(self, event=None):
        """ export list of problematic files"""
        buff = []
        for f, e in self.problematic:
            f = ":".join(f) # handle multiple files per ligand
            buff.append("%s,%s" % (f, e) )
        t = 'Select problematic log filename'
        ft = [("Any file type...", "*")] 
        idir = self.app._lastdir
        suggest = 'problematic_results.csv'
        fname = tfd.asksaveasfilename(parent=self.interior(), 
            title=t, filetypes=ft, initialdir=idir, initialfile=suggest)
        if not fname:
            return
        hf.writeList(fname, buff, addNewLine=1)


