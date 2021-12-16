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
#


import CADD.Raccoon2
# Raccoon stuff
import CADD.Raccoon2.HelperFunctionsN3P as hf
import RaccoonBasics as rb
import RaccoonEvents
import RaccoonPmvCamera 


import os, Pmw, glob
from PmwOptionMenu import OptionMenu as OptionMenuFix

import Tkinter as tk
import tkMessageBox as tmb
import tkFileDialog as tfd
from PIL import Image, ImageTk
import sys

# mgl modules
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction #as cb
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

class ConfigTab(rb.TabBase, rb.RaccoonDefaultWidget):
    
    def __init__(self, app, parent, debug=False):
        rb.TabBase.__init__(self, app, parent, debug = False)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.resource = self.app.resource
        self.dockengine = self.app.dockengine
        self.app.eventManager.registerListener(RaccoonEvents.SetDockingEngine, self.handleEngine)
        self.app.eventManager.registerListener(RaccoonEvents.ReceptorListChange, self.setReceptorList)
        self.app.eventManager.registerListener(RaccoonEvents.ReceptorListChange, self.nuke)

        self.camera = None # embedded camera object
        self._loaded_struct = []

        self._boxevent = RaccoonEvents.SearchConfigChange()
        self._searchevent = None # XXX TODO?
        
        # switch for loading multiple receptors in the viewer
        self.recLoaderMultiMode = tk.BooleanVar(value=False)
        self._currRec = []#  [ { 'name':xxxx, 'obj':[ rigid, flex ], 'fname':xxxx }, ... ]

        self.initIcons()
        self.makeInterface()



    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'system.png'
        self._ICON_sys = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'center_mol.png'
        self._ICON_center_mol = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'center_all.png'
        self._ICON_center_all = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'center_box.png'
        self._ICON_center_box = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'water.png'
        self._ICON_water = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'floppy.png'
        self._ICON_floppy = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'open.png'
        self._ICON_open = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'default.gif'
        self._ICON_default = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'singleMol.png'
        self._ICON_single = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'multiMol.png'
        self._ICON_multi = ImageTk.PhotoImage(Image.open(f))


    def handleEngine(self, event=None):
        """ handle widget display for different engines """
        #print "DD_CONFIG> EVENT notified that docking engine is now [%s]" % event.dockingengine
        self.dockengine = event.dockingengine


    def openConfig(self, fname = None):
        """ import data from a vina config """
        ad_ext = ("*.dpf", "*.DPF")
        ag_ext = ("*.gpf", "*.GPF")
        vina_ext = ("*.conf", "*.CONF")
        anyfile = ("Any file...", ("*"))
        if fname == None:
            if self.dockengine == 'vina':
                t = 'Select Vina config file to import'
                ftypes = [("Vina config file", vina_ext), anyfile ]                
            elif self.dockingengine == 'ad':
                t = 'Select AutoDock/AutoGrid parameter files to import'
                ftypes = [ ("AutoDock parameter file", ad_ext),
                           ("AutoGrid parameter file", ag_ext),
                            anyfile ]                
            fname = tfd.askopenfilename(parent=self.frame, title=t, filetypes = ftypes)
            if not fname: return
        #print "GOT FNAME[%s]" % fname

        if not fname: return
        # parse vina config
        if self.dockengine == 'vina':
            accepted = self._loadvinaconf(fname)
        # parse ad configs
        elif self.dockingengine =='ad':
            name, ext = os.path.splitext(fname)
            if ext.lower() == 'dpf':
                accepted = self._loaddpf(fname)
            elif ext.lower() == 'gpf':
                accepted = self._loadgpf(fname)
        t = 'Docking parameters'
        if len(accepted):
            m = ('The following docking parameters '
                 'have been accepted:\n\n%s' ) % ("\n".join(accepted))
            i = 'info'
        else:
            m = ('No docking parametes have been imported!\n'
                 'Inspect the config file and try again')
            i = 'error'
        tmb.showinfo(parent=self.frame, title=t, message=m, icon=i)
        self.app.eventManager.dispatchEvent(self._boxevent)
        # XXX TODO
        # self.app.eventManager.dispatchEvent(self._searchevent)
            

    def _loadvinaconf(self, fname, quiet=False):
        """ actual parser of vina CONF file """
        accepted = []
        # load data
        config = self.app.engine.gridBoxFromConf(fname)
        if not config:
            if not quiet:
                t = 'Config file error'
                m = ('There was an error loading the config file.\n'
                     'Inspect it and try again...')
                i = 'error'
                tmb.showinfo(parent=self.frame, title=t, message=m, icon=i)
            return False
        # center 
        center = [ config[k] for k in 'center_x', 'center_y', 'center_z' ]
        if self.app.engine.setBoxCenter(center):
            for i in range(3):
                self._thumbw_array[i].set( center[i])
            accepted.append('center')
        # size
        size = [ config[k] for k in 'size_x', 'size_y', 'size_z' ]
        if self.app.engine.setBoxSize(size):
            for i in range(3):
                self._thumbw_array[i+3].set( size[i])
            accepted.append('size')
        # search parms
        for k in ['exhaustiveness', 'num_modes', 'energy_range']:
            if not config[k] == None:
                v = config[k]
                self.app.engine.vina_settings[k] = v
                self.vinaWidgets[k].setvalue(v)
                accepted.append(k)
        # dispatch config EVENT
        #event = RaccoonEvents.SearchConfigChange()
        self.app.eventManager.dispatchEvent(self._boxevent)
        return accepted

    def _loaddpf(self, fname):
        """ """
        # load data
        # set widgets
        pass


    def _loadgpf(self, fname):
        """ """
        # load data
        # set widgets
        pass




    
    def saveConfig(self):
        """ """
        pass

    def setWheelBox(self, wheelname, value):
        """ wheel callback that sets center/size values in
            the docking engine
        """
        cx, cy, cz = self.app.engine.box_center
        sx, sy, sz = self.app.engine.box_size
        if wheelname=='center_x':
            cx = value
        elif wheelname=='center_y':
            cy = value
        elif wheelname=='center_z':
            cz = value
        elif wheelname=='size_x':
            sx = value
        elif wheelname=='size_y':
            sy = value
        elif wheelname=='size_z':
            sz = value
        self.app.engine.box_center = [ cx, cy, cz ]
        self.app.engine.box_size = [ sx, sy, sz ]

        for i in self.app.engine.box_center :
            if i == None:
                return
        self.Box3D.Set(center = (cx, cy, cz))
        self.Box3D.Set(xside=sx, yside=sy , zside=sz)
        self.app.eventManager.dispatchEvent(self._boxevent)

        # if a full triplet is defined, sync the data with the engine config internals
        if not None in self.app.engine.box_center:
            self.app.engine.setBoxCenter( self.app.engine.box_center )
        if not None in self.app.engine.box_size:
            self.app.engine.setBoxSize( self.app.engine.box_size )

    def makeInterfaceLocal(self):
        """filler for now"""
        pass
    
    def makeInterfaceOpal(self):
        """ """
        pass

    def makeInterface(self):
        """ create interface for ssh """
        self.resetFrame()
        
        colors = { 'center_x' : '#ff3333',
                   'center_y' : 'green',
                   'center_z' : '#00aaff',
                   'size_x' : '#ff3333',
                   'size_y' : 'green',
                   'size_z' : '#0099ff',
                   }

        frame_set = {  'ring_bd' : 1, 'ring_highlightbackground' :'black', 'ring_borderwidth' : 2, 
                    'ring_highlightcolor' : 'black', 'ring_highlightthickness' : 1, 'ring_relief' : 'flat', 
                    'groupchildsite_bg':'white', 'groupchildsite_relief':'sunken','ring_bg':'white',
                        'tag_bd' : '1', 'tag_highlightbackground' :'black', 'tag_borderwidth':2, 
                        'tag_highlightcolor' : 'black', 'tag_highlightthickness': 1}

        frame_set = { 'ring_bd' : 1, 'ring_highlightbackground' :'black', 'ring_borderwidth' : 2, 
                    'ring_highlightcolor' : 'black', 'ring_highlightthickness' : 1, 'ring_relief' : 'flat'}

        frame_set = {}
        bset = { 'bg' : '#95bed5', 'width' : 22, 'height': 22, 'relief' : 'raised'}
        bset = { 'bg' : '#2e363b', 'width' : 22, 'height': 22, 'relief' : 'raised'}
        bset = { 'bg' : '#a6abae', 'width' : 22, 'height': 22, 'relief' : 'raised'}
        bset = { 'bg' : '#969b9d'  } # 'width' : 22, 'height': 22, 'relief' : 'raised'}
        bset = {}
        bset.update(self.BORDER)

        # left frame
        lframe = tk.Frame(self.frame)
        # button tollbar 
        tk.Frame(lframe, height=7).pack(expand=0, fill='x', padx=0, pady=0, side='top', anchor='n')
        # minispacer

        bframe = tk.Frame(lframe)
        b = tk.Button(bframe, text='Load...', command = self.openConfig, image= self._ICON_open, compound='left',
            height=14,**bset)
        b.pack(expand=1,fill='x', anchor='w', side='left',padx=1)

        b.pack(expand=1,fill='x', anchor='w', side='left',padx=1)
        bframe.pack(expand=0, fill='x', padx=0, pady=0, side='top', anchor='n')
        ########################## center wheels
        self._thumbw_array = []
        c_group = Pmw.Group(lframe, tag_text='Center', tag_font=self.FONTbold, **frame_set)
        for lab in ['center_x', 'center_y', 'center_z']:
            cb = CallbackFunction(self.setWheelBox, lab)
            tw = ThumbWheel(
                c_group.interior(), labCfg={'text':lab, 'side':'left','fg':colors[lab],
                'bg':'black', 'width':9 }, showLabel=1,
                width=90, height=14, type=float, value=0.0,
                callback=cb, continuous=True,
                oneTurn=5, wheelPad=0)
            tw.pack(side='top', pady=2,anchor='n')
            self._thumbw_array.append(tw)
        c_group.pack(side='top', anchor='n', expand=0,fill='x',ipadx=2,ipady=3, padx=1)

        ########################## size wheels
        s_group = Pmw.Group(lframe, tag_text='Size', tag_font=self.FONTbold, **frame_set)
                     
        for lab in ['size_x', 'size_y', 'size_z']:
            cb = CallbackFunction(self.setWheelBox, lab)
            tw = ThumbWheel(
                s_group.interior(), labCfg={'text':lab, 'side':'left','fg':colors[lab],
                'bg':'black', 'width':9 }, showLabel=1,
                width=90, height=14, type=float, value=0.0, min=0.0001,
                callback=cb, continuous=True,
                oneTurn=5, wheelPad=0)
            tw.pack(side='top', pady=2,anchor='n')
            self._thumbw_array.append(tw)
        s_group.pack(side='top', anchor='n', expand=0,fill='x',ipadx=2,ipady=3, padx=1,pady=2)

        ########################## search settings
        self.searchparmgroup = Pmw.Group(lframe, tag_text='Search parameters', tag_font=self.FONTbold, **frame_set)
        # autodock search parms
        self.buildSearchADPanel(target = self.searchparmgroup )
        # vina search parms
        self.buildSearchVinaPanel(target = self.searchparmgroup )

        self.searchparmgroup.pack(side='top', anchor='n', expand=0,fill='x',ipadx=2,ipady=3, padx=1,pady=5)

        ########################## Receptors
        self._receptors_group = Pmw.Group(lframe, tag_text='Receptor list', tag_font=self.FONTbold,collapsedsize=3, **frame_set)
        # important
        self.receptorListbox = Pmw.ScrolledListBox(self._receptors_group.interior(), listbox_highlightbackground = 'black',
            # selectioncommand=self.loadreceptor, 
            listbox_selectbackground='yellow')
        self.receptorListbox.pack(expand=1, fill='both',padx=3, pady=0)
        self.receptorListbox.component('listbox').bind('<ButtonRelease-1>', self.loadreceptor)
        self.receptorListbox.component('listbox').bind('<Button-3>', self._delreceptor)

        tb = tk.Frame(self._receptors_group.interior())
        # single-multi load buttons
        self.recLoaderMode_single = tk.Radiobutton(tb, text='Single', image = self._ICON_single, indicatoron=False, 
            variable=self.recLoaderMultiMode, value = False, compound='left', height=16, **bset)
        self.recLoaderMode_single.pack(anchor='n', side='left',pady=1,expand=1,fill='x',padx=1)
        self.recLoaderMode_multi = tk.Radiobutton(tb, text='Multi', image = self._ICON_multi, indicatoron=False,
            variable=self.recLoaderMultiMode, value = True, compound='left', height=16, **bset)
        self.recLoaderMode_multi.pack(anchor='n', side='left',pady=1,expand=1,fill='x',padx=1)
        

        tb.pack(expand=0, fill='x',anchor='s',side='bottom',padx=3)

        self._receptors_group.pack(side='bottom', anchor='n', expand=1, fill='both',ipadx=4,ipady=4, padx=1,pady=0)

        lframe.pack(side = 'left', anchor='n', expand='n', fill='y', padx=0, pady=0)

        ###### 3D Viewer
        rframe = tk.Frame(self.frame)
        spacer = tk.Frame(rframe, width=5) #, bg='red')
        spacer.pack(expand=0,fill='y',side='left',anchor='w')
        spacer.pack_propagate(0)
        vgroup = Pmw.Group(rframe, tag_text = '3D viewer', tag_font=self.FONTbold,groupchildsite_bg='black',  **frame_set)

        # TOOLBAR
        vtoolbar = tk.Frame(vgroup.interior())
        vtoolbar.pack(side='left', anchor='w', expand=0, fill='y')
        cb = CallbackFunction(self.centerView, None)
        tk.Button(vtoolbar, text='Center\nall', image = self._ICON_center_all, width=22, height=22, 
            command=cb, **bset).pack(anchor='n', side='top')
        cb = CallbackFunction(self.centerView, 'mol')
        tk.Button(vtoolbar, text='Center\nmol', image = self._ICON_center_mol, width=22, height=22,
            command=cb, **bset ).pack(anchor='n', side='top')
        cb = CallbackFunction(self.centerView, 'box')
        tk.Button(vtoolbar, text='Center\nbox', image = self._ICON_center_box, width=22, height=22,
            command=cb, **bset ).pack(anchor='n', side='top',pady=1)
        # 3d Viewer settings XXX TODO
        #tk.Button(vtoolbar, text='Settings', image = self._ICON_sys, width=22, height=22, **bset).pack(anchor='n', side='top')
        vgroup.pack(side='right', anchor='e', expand=1, fill='both', padx=0, pady=0)

        # 3D viewer  
        self.make3Dboxviewer(vgroup.interior())

        rframe.pack(side = 'right', anchor='n', expand=1, fill='both',padx=0, pady=0)
        
        if self.app.dockengine == 'vina':
            self.setSearchParmsVina()
        elif self.app.dockengine == 'autodock':
            self.setSearchParmsAD()
        self.frame.pack(expand=1, fill='both',anchor='n', side='top')

    def _delreceptor(self, event=None):
        """ """
        return
        # XXX TODO TO REMOVE RECEPTORS FROM HERE
        parent = self.receptorListbox 
        try:
            sel = parent.getvalue()
            #print "SEL", sel
            menu = tk.Menu(parent=parent, tearoff=False, takefocus=1)
            txt = 'Delete "%s"' % sel
            menu.add_command(txxt, state='normal', command = self.receptor)
        except:
            #print "nothing"
            pass


    def make3Dboxviewer(self, target):
        """ create the config camera and add the default box object"""
        # grid cam name 
        name = 'gridcam'
        if self.app.viewer == None:
            # XXX reinitialize fonts?
            self.app.viewer = RaccoonPmvCamera.EmbeddedMolViewer()
            self.app.molviewer = self.app.viewer.mv
            self.app.parent.bind_all('<F12>', self.app.viewer.togglepmv)
        # adding config camera
        if self.camera == None:
            self.camera = self.app.viewer.addCamera(target, name)
            self.camera_name = name
            from DejaVu.Box import Box
            from MolKit import Read
            self.Box3D = Box('Grid_box')
            self.Box3D.Set(xside=0.001, yside=0.001, zside=0.001)
            self.app.molviewer.GUI.VIEWER.AddObject(self.Box3D)        
            self.app.viewer.cameras[name]['structures'].append(self.Box3D)


    def centerView(self, target=None, event=None):
        """ center view in the 3D config viewer"""
        #root = self.app.viewer.rootObject
        showBox = False
        if target == 'box':
            print "Center box"
            item = self.Box3D
        elif target == 'mol':
            print "center mol"
            self.Box3D.visible = False
            item = None
            showBox = True
        else:
            print "CENTER ALL"
            item = None
        self.app.viewer.centerView(item)
        if showBox:
            self.Box3D.visible = True
            

    def getRecLoaderMode(self):
        """ check the value of variable self.recLoaderMultiMode 
            True  : keep adding receptors to the current
            False : delete previous receptors upon loading of the selected one
        """
        return self.recLoaderMultiMode.get()


    def loadreceptor(self, event=None):
        """ load the receptor in the viewer deleting previous mols
            if necessary
        """
        # TOP
        # TOP ######################
        self.receptorListbox.component('listbox').unbind('<ButtonRelease-1>')
        try:
            recname = self.receptorListbox.getvalue()[0]
        except:
            self.receptorListbox.component('listbox').bind('<ButtonRelease-1>', self.loadreceptor)
            return
        mode = 'single'
        if self.recLoaderMultiMode.get() == 1:
            mode = 'multi'
        cam = self.camera_name
        viewer = self.app.viewer
        #print "Loading rec", recname,
        #print "MODE", mode

        self.app.setBusy()

        if mode == 'single' and len(self._currRec)>1:
            # delete non-main 
            for i in range(len(self._currRec)-1):
                obj = self._currRec[i+1]['obj']
                for o in obj: viewer.deleteInCamera(o,cam)
                self._currRec.pop(i+1)

        recfiles = self.app.engine.getRecFiles(recname)
        recfname = recfiles[0]

        for i in range(len(self._currRec)):
            rec = self._currRec[i]
            if (rec['name'] == recname) and (rec['fname'] == recfname):
                if i == 0:
                    # already loaded and main
                    self.receptorListbox.component('listbox').bind('<ButtonRelease-1>', self.loadreceptor)
                    self.app.setReady()
                    return
                else:
                    # already loaded but not main
                    # put selected mol as first
                    self._currRec = [ self._currRec[i] ] + self._currRec[:i] + self._currRec[i+1:]
                    # FIXME apply STYLES (main, secondary)
                    self.app.setReady()
                    return
        # the current main is not the selected one
        if mode == 'single' and len(self._currRec) > 0:
            obj = self._currRec[0]['obj']
            for o in obj: viewer.deleteInCamera(o, cam)
            self._currRec = []
        newrec = { 'name' : recname, 'fname' : recfname }
        newrec['obj'] = [ viewer.loadInCamera(f, cam) for f in recfiles ]
        self._currRec = [newrec] + self._currRec
        self.receptorListbox.component('listbox').bind('<ButtonRelease-1>', self.loadreceptor)
        self.app.setReady()

    def nuke(self, event=None):
        """ remove all currently loaded receptors"""
        # we need to protect the box!
        #print "NUKE CALLED"
        for rec in self._currRec:
            #print "DELETING REC", rec
            for o in rec['obj']:
                self.app.viewer.deleteInCamera(o, self.camera_name)
        self._currRec = []

            
    def buildSearchVinaPanel(self, target):
        """ create the panel with vina search settings""" 
        try:
            # avoid double packaging
            self.searchParmVinaPanel
            return
        except:
            f = self.searchParmVinaPanel = tk.Frame(target.interior())
            target.configure(tag_text = 'Search parameters [ VINA ]')

        self.vinaWidgets = {}
        # exhaustiveness
        tk.Label(f, text='exhaustiveness', width =15,anchor='e').grid(row=1,column=1,sticky='we',padx=5)
        self.searchParmVina_exhaustiveness = Pmw.EntryField( f, validate = hf.validatePosNonNullInt,
            entry_justify='right', entry_width=8)
        self.searchParmVina_exhaustiveness.grid(row=1, column=2,sticky='we',columnspan=1)
        def d(event=None): self.setDefSearchParmVina('exhaustiveness')
        tk.Button(f, text='D', image=self._ICON_default, command=d).grid(row=1,column=3, sticky='e')
        self.vinaWidgets['exhaustiveness'] = self.searchParmVina_exhaustiveness


        # num modes
        tk.Label(f, text='num.modes', width =15,anchor='e').grid(row=2,column=1,sticky='we',padx=5)
        self.searchParmVina_nummodes = Pmw.EntryField( f, validate = hf.validatePosNonNullInt,
            entry_justify='right', entry_width=8)
        self.searchParmVina_nummodes.grid(row=2, column=2,sticky='we',columnspan=1)
        def d(event=None): self.setDefSearchParmVina('num.modes')
        tk.Button(f, text='D',image=self._ICON_default, command=d).grid(row=2,column=3, sticky='e')
        self.vinaWidgets['num_modes'] = self.searchParmVina_nummodes

        # energy range
        tk.Label(f, text='energy range', width =15,anchor='e').grid(row=3,column=1,sticky='we',padx=5)
        self.searchParmVina_energyrange = Pmw.EntryField( f, validate = hf.validateFloatPos, 
            entry_justify='right', entry_width=8)
        self.searchParmVina_energyrange.grid(row=3, column=2,sticky='we',columnspan=1)
        def d(event=None): self.setDefSearchParmVina('energy range')
        tk.Button(f, text='D', image=self._ICON_default,command=d).grid(row=3,column=3, sticky='e')
        self.vinaWidgets['energy_range'] = self.searchParmVina_energyrange

        # executed only the first time
        self.setDefSearchParmVina()


    def buildSearchADPanel(self, target):
        """ create the panel with autodock search settings""" 
        try:
            # avoid double packaging
            self.searchParmADPanel
            return
        except:
            f = self.searchParmADPanel = tk.Frame(target.interior())
            target.configure(tag_text = 'Search parameters [ AD ]')

        tk.Label(f, text='GA SETTINGS SHOULD BE HERE', width =15,anchor='w').grid(row=2,column=1,sticky='we')
        self.setDefSearchParmAD()

        
    def setDefSearchParmVina(self, request = None):
        """ """
        
        #widgets =  [ self.searchParmVina_exhaustiveness,
        #             self.searchParmVina_nummodes,
        #             self.searchParmVina_energyrange ]
        values = []
        wid = []
        if request in ['exhaustiveness', None]:
            values.append(8)
            wid.append(self.vinaWidgets['exhaustiveness'])
        if request in ['num_modes', None]:
            values.append(9)
            wid.append(self.vinaWidgets['num_modes'])
        if request in ['energy_range', None]:
            values.append(3)
            wid.append(self.vinaWidgets['energy_range'])
        for i in range(len(values)):
            wid[i].setentry(values[i])        

    def setDefSearchParmAD(self, value = None):
        #print "NO DEFAUILT SETTINGS FOR AD YET"
        return
        

    def setSearchParmsVina(self):
        """ pack and activate the search parms panel for vina """
        self.searchParmADPanel.pack_forget()
        self.searchParmVinaPanel.pack(expand=0,fill='x',anchor='n',padx=0, pady=0)


    def setSeachParmsAD(self):
        """ pack and activate the search parms panel for autodock """
        self.searchParmVinaPanel.pack_forget()
        self.searchParmADPanel.pack(expand=0,fill='x',anchor='n',padx=0, pady=0)


    def getSearchParmVina(self):
        """ """
        widgets =  [ self.searchParmVina_exhaustiveness, self.searchParmVina_nummodes,
                     self.searchParmVina_energyrange ]
        for w in widgets:
            if not w.valid():
                return False
        return  { 'exhaustiveness': self.searchParmVina_exhaustiveness.getvalue(),
                  'num.modes' : self.searchParmVina_nummodes.getvalue(),
                  'energyrange': self.searchParmVina_energyrange.getvalue(),
                }

    def getSearchParmAD(self):
        """ """ 
        # walk through ad parms and return settings
        pass


    def setReceptorList(self, event=None):
        """update the list of receptors shown in the picker for the config
            settings
        """
        self.receptorListbox.clear()
        self.receptorListbox.setlist(sorted(self.app.engine.RecBook.keys()) )


