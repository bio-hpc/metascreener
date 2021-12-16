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
import CADD.Raccoon2.HelperFunctionsN3P as hf
import RaccoonBasics as rb
import RaccoonEvents
import DebugTools
import os, Pmw, glob, sys
from PmwOptionMenu import OptionMenu as OptionMenuFix
import Tkinter as tk
import tkMessageBox as tmb
import tkFileDialog as tfd
from PIL import Image, ImageTk

# mgl modules
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction #as cb


# TODO add an arbitrary distance constraint?
# TODO add pharmacophore score


class InteractionFilterWidget(rb.RaccoonDefaultWidget, DebugTools.DebugObj, tk.Frame):
    """ provide the interaction filter widget
        with different types:

            HBa
            HBd
            HB
            Metal
            vdW
            Pi-stack
            T-stack
            Generic stack
           
   checkbutton   pulldown     entry    button (remove)
        [x] | | [type..] | [ string ] [ x ]
    """
    def __init__(self, parent, manager, settings={}, color=None, debug = False): #, destroy_cb):
        self.color = '#bbff33'
        self.color = color # differenciate filter types?
        rb.RaccoonDefaultWidget.__init__(self, parent) 
        DebugTools.DebugObj.__init__(self, debug)
        tk.Frame.__init__(self, master=self.parent, relief='raised', bg=color,  **self.BORDER)
        self.manager = manager
        self._widgets = [self]

        self.initIcons()
        self.destroy_cb = None # destroy_cb
        self.eventManager = self.manager.eventManager
        #self.eventManager = eventManager
        #self.event = RaccoonEvents.FilterSetSelection()

        self.settings = settings
        self.build()
        self.setfilter()

        # hack to have mouse wheel to work all the time
        for w in self._widgets:
            w.bind("<Button-4>", self.manager.mousescroll)
            w.bind("<Button-5>", self.manager.mousescroll)
            if hasattr(w, 'components'):
                for c in w.components():
                    w.component(c).bind("<Button-4>", self.manager.mousescroll)
                    w.component(c).bind("<Button-5>", self.manager.mousescroll)


    def build(self):
        """ build the widgets"""
        entry_width = 10

        # types strings
        self._notype = '< select type >'
        self.stringToType = { 
                        'HB donor' : 'hbd',
                        'HB acceptor' : 'hba',
                        'HB any' : 'hb',
                        'Metal coord': 'metal',
                        'vdW contact': 'vdw',
                        'Pi-stacking': 'ppi', # XXX check this
                        'T-stacking' : 'tpi', # XXX check this
                        'Any stacking': 'pi', # XXX check this
                    }
        self.typeToString = {}
        for k,v in self.stringToType.items():
            self.typeToString[v] = k

        # active checkbutton
        self.active_var = tk.BooleanVar(value=False)
        self.active = tk.Checkbutton(self, variable=self.active_var, 
            bg=self.color, command=self.trigger)
        #self.active.pack(side='left', anchor='w', expand=0, fill='none')

        # interaction type
        self.typeChoice = OptionMenuFix(self,
            menubutton_font = self.FONT,
            menubutton_bg = self.color,
            menu_font = self.FONT,
            menubutton_width = 15,
            menubutton_bd = 1, menubutton_highlightbackground = 'black',
            menubutton_borderwidth=1, menubutton_highlightcolor='black', 
            menubutton_highlightthickness = 1,
            menubutton_height=1,
            command = self.trigger, # self.typeValidator, # self.trigger,
            items = sorted(self.stringToType.keys())
            )
        self.typeChoice.setvalue(self._notype)
        self.typeChoice.pack(side='left', anchor='w', expand=1, fill='x', padx=3, pady=1)
        self._widgets.append(self.typeChoice)

        # strings
        f = tk.Frame(self) # nested frames to have a decent alignment (Tk sucks(TM) )
        ef = tk.Frame(f) 
        # chain
        self.chain = Pmw.EntryField(ef, entry_font=self.FONT,
            labelpos = 'n', label_font=self.FONT, label_text='chain',
            hull_bg = self.color,
            entry_width=4, entry_justify='center',
            entry_bd = 1, entry_highlightbackground = 'black',
            entry_borderwidth=1, entry_highlightcolor='black', 
            entry_highlightthickness = 1,
            )
        self.chain.pack(side='left', anchor='n', expand=0, fill='x', padx=3 )
        self.chain.component('entry').bind('<Return>', self.return_cb)
        self.chain.component('entry').bind('<Leave>', self.focusLeave_cb)
        self._widgets.append(self.chain)

        # residue
        self.residue = Pmw.EntryField(ef, entry_font=self.FONT,
            labelpos = 'n', label_font=self.FONT, label_text='residue',
            hull_bg = self.color,
            entry_width=entry_width, entry_justify='center',
            entry_highlightbackground = 'black',
            entry_borderwidth=1, entry_highlightcolor='black', 
            entry_highlightthickness = 1,
            )
        self.residue.pack(side='left', anchor='n', expand=1, fill='x', padx=3)
        self.residue.component('entry').bind('<Return>', self.return_cb)
        self.residue.component('entry').bind('<Leave>', self.focusLeave_cb)
        self._widgets.append(self.residue)

        # atom
        self.atom = Pmw.EntryField(ef, entry_font=self.FONT,
            labelpos = 'n', label_font=self.FONT, label_text='atom',
            hull_bg = self.color,
            entry_width=entry_width, entry_justify='center',
            entry_highlightbackground = 'black',
            entry_borderwidth=1, entry_highlightcolor='black', 
            entry_highlightthickness = 1,
            )
        self.atom.pack(side='left', anchor='n', expand=1, fill='x', padx=3)
        self.atom.component('entry').bind('<Return>', self.return_cb)
        self._widgets.append(self.atom)

        s = tk.Frame(f, height=15)
        s.pack(side='bottom', anchor='w', expand=1, fill='both')

        ef.pack(side='top', anchor='w', expand=1, fill='x', padx=3)
        f.pack(side='left', anchor='w', expand=1, fill='both')

        self._widgets.append(s)
        self._widgets.append(ef)
        self._widgets.append(f)


        # wanted/not wanted
        self.wanted = True
        self.wantedButton = tk.Button(self, font=self.FONTbold, image=self._ICON_filtoff, relief='flat')
        selmenu = [ None,
                    ['wanted', 'normal', self.setPositive],
                    ['not wanted', 'normal', self.setNegative],
                    ['disable', 'normal', self.setOff],
                  ]
        menu = rb.RacMenu(self.wantedButton, selmenu, placement='under')
        self.wantedButton.pack(side='left', anchor='w', expand=0, fill='none', padx=1, pady=1)
        self._widgets.append(self.wantedButton)


        # destroy button
        self.destruction = tk.Button(self, text="X", image=self._ICON_del, command=self.destroy,
            bg=self.color,
            relief='flat') #,width=22) #, **self.BORDER)
        self.destruction.pack(side='left', anchor='w', expand=0, fill='none')
        self._widgets.append(self.destruction)


    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH

        f = icon_path + os.sep + 'removeSmall.png'
        f = icon_path + os.sep + 'removeSmallbw.png'
        self._ICON_del = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'filt_positive.png'
        f = icon_path + os.sep + 'filt_positiveLight.png'
        self._ICON_filtpos = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'filt_negativeLight.png'
        self._ICON_filtneg = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'filt_inactiveLight.png'
        self._ICON_filtoff = ImageTk.PhotoImage(Image.open(f))


    def setPositive(self, event=None):
        """ set the interaction to be wanted"""
        self.wanted = True
        self.wantedButton.configure(image=self._ICON_filtpos, text='A')
        self.enable()
        #self.trigger()

    def setNegative(self, event=None):
        """ set the interaction to be not wanted"""
        self.wanted = False
        self.wantedButton.configure(image=self._ICON_filtneg, text='R')
        self.enable()
        #self.trigger()

    def setOff(self, event=None):
        """ turn off the filter"""
        self.wantedButton.configure(image=self._ICON_filtoff, text='R')
        current = self.active_var.get()
        self.active_var.set(False)
        # the filter was active, it has been disabled
        # so we need to send event for filterEngine to
        # be triggered
        if not self.active_var.get() == current:
            self.sendEvent()
        
    def return_cb(self, event=None):
        """ function called when return is pressed
            in the text fields
        """
        if self.wanted == True:
            self.setPositive()
        else:
            self.setNegative()

    def focusLeave_cb(self, event=None):
        """ trigger status check for entries
            when they loose focus
            Important when the filter has been alread
            activated, then the user changes the text in the
            field
        """
        if not self.isActive():
            return
        self.entryValidator(quiet=False)

    def isActive(self, event=None):
        """ return if the filter is active"""
        return self.active_var.get()

    def disable(self, event=None):  
        """ disable the filter"""
        self.active_var.set(False)

    def enable(self, event=None, quiet=True):  
        """ enable the filter"""
        self.active_var.set(True)
        self.trigger(quiet=quiet)

    def entryValidator(self, string=None, quiet=True):
        """ validate the text entry field
        """
        #if string == None:
        #    string = self.entry.getvalue()
        chain = self.chain.getvalue().strip()
        res = self.residue.getvalue().strip()
        atom = self.atom.getvalue().strip()
        if not chain and not res and not atom:
            self.setOff()
            if not quiet:
                t = 'Interaction specification not valid'
                i = 'error'
                m = ('The interaction must be defined by typing at '
                     'least a chain, residue or atom string.\n'
                     'Single character "?" and multi-character "*" wildcards can be used.'
                    ) 
                tmb.showinfo(parent=self, title=t, icon=i, message=m)
            return False
        return True


    def typeValidator(self, string=None, quiet=False):
        """ validate type selection """
        _type = self.typeChoice.getvalue()
        if _type == self._notype:
            if not quiet:
                t = 'Filter type error'
                i = 'warning'
                m = ('An interaction type must be selected')
                tmb.showinfo(parent=self, title=t, icon=i, message=m)
            self.setOff()
            return False        
        return True

    def isvalid(self, quiet=True):
        """return if the entry is valid"""
        typeCheck = self.typeValidator(quiet=quiet) 
        if not typeCheck: # or not self.isActive():
            return
        if not self.isActive():
            return
        entryCheck = self.entryValidator(quiet=quiet)
        return (typeCheck and entryCheck)

    def trigger(self, event=None, quiet=False):
        """ command executed when the filter is activated"""
        #curr_state = self.isActive() # active_var.get()
        if not self.isvalid(quiet=quiet):
            return
        self.active_var.set(True)
        self.sendEvent()

    def sendEvent(self):
        """ trigger the event"""
        e = RaccoonEvents.FilterInteractionEvent()
        self.eventManager.dispatchEvent(e)

    def getType(self):
        """ return interaction type"""
        return self.stringToType[ self.typeChoice.getvalue() ]

    def getPattern(self):
        """ return interaction text pattern"""
        c = self.chain.getvalue().strip()
        r = self.residue.getvalue().strip()
        a = self.atom.getvalue().strip()
        if c == "": c = "*"
        if r == "": r = "*"
        if a == "": a = "*"
        return "%s:%s:%s" % (c,r,a)


    def setfilter(self, settings={}):
        """ initialize filter with requested values"""
        if settings == {}:
            settings == self.settings
        if settings == {}:
            return
        t = self.settings['type']
        t = self.typeToString[t]
        e = self.settings['patter']
        self.typeChoice.setvalue(t)
        self.entry.setvalue(e)
        if self.isvalid(): self.active_var.set(True)
        # FIXME set this to active?
        #return { 'type' : t, 'pattern' : e }



    def destroy(self, event=None):
        """ remove itself from the list of filters
            and unpack the widget
        """
        t = 'Delete filter'
        i = 'info'
        m = ('Remove this filter?')
        if self.isvalid():
            if not tmb.askyesno(parent=self, title=t, message=m, icon=i):
                return
        self.destroy_cb()


class InteractFiltManager(rb.RaccoonDefaultWidget, DebugTools.DebugObj, Pmw.Group):
    """ provide the interaction filters manager widget

    """
    def __init__(self, parent, update_cb=None, debug=False): #, destroy_cb):

        rb.RaccoonDefaultWidget.__init__(self, parent)
        DebugTools.DebugObj.__init__(self, debug)
        Pmw.Group.__init__(self, parent=parent, tag_text = 'Target interactions', tag_font=self.FONTbold,
        
              ring_border=1, ring_highlightcolor='black', ring_highlightbackground='black',
            ring_highlightthickness=1,ring_relief='flat')      
        
        self.eventManager = RaccoonEvents.RaccoonEventManager()
        self.eventManager.registerListener(RaccoonEvents.FilterInteractionEvent, self.update)
        self.initIcons()
        self.filters = []
        self.update_cb = update_cb

        self.container = tk.Frame(self.interior()) # this contains the widgets on the left

        # build toolbar
        self.toolbar = tk.Frame(self.container)
        # add button
        b = tk.Button(self.toolbar, text='+', image=self._ICON_add, command=self.add, **self.BORDER)
        b.pack(anchor='w', side='left')
        # remove button
        b = tk.Button(self.toolbar, text='-', image=self._ICON_del, **self.BORDER)
        b.pack(anchor='w', side='left',padx=1)
        selmenu = [ None,
                    ['Remove inactive', 'normal', self.removeInactive],
                    ['Remove all', 'normal', self.nuke],
                  ]
        menu = rb.RacMenu(b, selmenu, placement='under')



        # selection button menu
        b = tk.Button(self.toolbar, text='s', image=self._ICON_selmenu, **self.BORDER)
        b.pack(anchor='w', side='left',padx=0)
        selmenu = [ None,
                    ['Activate all', 'normal', self.setAllActive],
                    ['Deactivate all', 'normal', self.setAllInactive],
                    ['Invert active/inactive', 'normal', self.invertStatus],
                  ]
        menu = rb.RacMenu(b, selmenu, placement='under')

        # mode pulldown
        self._mode_choices = { 'match all': 'all', 'match any': 'any'}
        self.modeChoice = OptionMenuFix(self.toolbar,
            menubutton_font = self.FONT,
            menu_font = self.FONT,
            menubutton_width = 10,
            menubutton_bd = 1, menubutton_highlightbackground = 'black',
            menubutton_borderwidth=1, menubutton_highlightcolor='black', 
            menubutton_highlightthickness = 1,
            menubutton_height=1,
            #command = self.trigger,
            items = sorted(self._mode_choices.keys(), reverse=True),
            )
        f = tk.Frame(self.toolbar)
        self.labelActiveFilt = tk.IntVar(value='0')
        tk.Label(f, text='active filters:', font=self.FONT).pack(anchor='w',side='left')
        tk.Label(f, textvar=self.labelActiveFilt, font=self.FONTbold).pack(anchor='w',side='left')
        f.pack(anchor='w', side='left', padx=15)
        self.modeChoice.pack(anchor='w', side='right', padx=1)
        self.toolbar.pack(anchor='w', side='top', expand=1, fill='x', padx=4, pady=2)

        # build filter filtFrame
        self.filtFrame = Pmw.ScrolledFrame(self.container, horizflex='expand', # vertflex='expand', 
                vscrollmode='static', hscrollmode='dynamic')
        #self.filtFrame.component('hull').configure(**self.BORDER)
        self.filtFrame.component('clipper').configure(bg='white')
        self.filtFrame.component('frame').configure(relief='flat', bg='white')
        #self.filtFrame.component('vertscrollbar').bind("<Button-4>", self.mousescroll)
        for c in [ 'borderframe', 'clipper', 'frame', 'horizscrollbar', 'hull', 'vertscrollbar']:
            self.filtFrame.component(c).bind("<Button-4>", self.mousescroll)
            self.filtFrame.component(c).bind("<Button-5>", self.mousescroll)
        self.interior().bind("<Button-4>", self.mousescroll)
        self.interior().bind("<Button-5>", self.mousescroll)

        self.filtFrame.pack(anchor='w', side='top', expand=1, fill='both',padx=4, pady=2)

        self.container.pack(anchor='w',side='left', expand=1, fill='both')

        self.percentageFrame = tk.Frame(self.interior()) # this contains the widgets on the right

        # pie
        self.pie = hf.PercentPie(self.percentageFrame, radius=50)
        self.pie.pack(anchor='n', side='top', padx=5, pady=5)
        #self.pie.set_percent(20)

        # passed label
        f = tk.Frame(self.percentageFrame)
        tk.Label(f, text='passed :', font=self.FONTbold).pack(side='left',anchor='w')
        self.statusLabel = tk.Label(f, text='0', width=8, anchor='w', font=self.FONT)
        self.statusLabel.pack(side='left', anchor='w')
        f.pack(anchor='n', side='top')

        #self.percentageFrame.pack(anchor='e',side='left', expand=1, fill='y')
        self.percentageFrame.pack(expand=0,fill=None, anchor='e', side='left')

    def setpassed(self, count, percentage):
        """ set the numerical value of 
            items that passed this filter
        """
        self.statusLabel.configure(text=count)
        self.pie.set_percent(percentage)    


    def setAllActive(self, event=None):
        """ set all filters active"""
        change = False
        for o in self.filters:
            if not o.isActive():
                o.enable(quiet=True)
                if o.isActive():
                    change = False
        if change:
            e = RaccoonEvents.FilterInteractionEvent()
            self.eventManager.dispatchEvent(e)

    def setAllInactive(self, event=None):
        """ set all filters inactive"""
        change = False
        for o in self.filters:
            if o.isActive():
                o.disable()
                change = True
        if change:
            e = RaccoonEvents.FilterInteractionEvent()
            self.eventManager.dispatchEvent(e)        

    def invertStatus(self, event=None):
        """ invert filter status"""
        change = False
        for o in self.filters:
            if o.isActive():
                o.disable()
                change = True
            else:
                o.enable(quiet=True)
                if o.isActive():
                    change = True
        if change:
            e = RaccoonEvents.FilterInteractionEvent()
            self.eventManager.dispatchEvent(e)


    def countActive(self, event=None):
        """ update count label of active filters"""
        c = 0
        for o in self.filters:
            if o.active_var.get():
                c+= 1
        self.labelActiveFilt.set(c)

    def mousescroll(self, event):
        """ manage mousescroll events"""
        if event.num == 5 or event.delta == -120:
            self.filtFrame.yview(tk.SCROLL, +1, tk.UNITS)
        if event.num ==4 or event.delta == 120:
            self.filtFrame.yview(tk.SCROLL, -1, tk.UNITS)



    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH

        f = icon_path + os.sep + 'removeSmall.png'
        self._ICON_del = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'addSmall.png'
        self._ICON_add = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'select_menu.png'
        self._ICON_selmenu = ImageTk.PhotoImage(Image.open(f))
        
        
    def add(self, event=None, settings={}):
        """ add a new filter widget
            if settings is not empty, the new filter
            will be initialized with the specified values
        """
        f = InteractionFilterWidget( self.filtFrame.interior(), 
            manager = self, settings=settings)
        cb = CallbackFunction(self.destroy, f)
        f.destroy_cb = cb
        self.filters.append(f)
        f.pack(anchor='w', side='top', padx=2, pady=1, expand=1,fill='x')
        # NOTE no event when adding (empty filter!) nor when 
        #      settings are restored, otherwise restoting a pre-saved
        #      set of multi-interaction settings will trigger 
        #      a lot of filter updates (i.e. troubles, when many ligands
        #      are loaded.
        #       the function creating 
        #      the filter (i.e. FiltSettingManager) should
        #      take care of populating all filters first
        #      *then* initial kick is given.
        # trigger event # XXX no! it's empty
        #if not settings == {}
        #    e = RaccoonEvents.FilterInteractionEvent()
        #    self.eventManager.dispatchEvent(e)

    def nuke(self, event=None, quiet=False):
        """ remove all the filters at once"""
        if len(self.filters) ==0 : return
        if not quiet:
            for o in self.filters:
                if o.isActive():
                    t = 'Remove all filters'
                    i = 'info'
                    m = ('All interaction filters are going to be removed.\n\nAre you sure?')
                    if not tmb.askyesno(parent=self.interior(), title=t, message=m, icon=i):
                        return
                    break
        for o in self.filters:
            o.pack_forget()
        self.filters = []
        e = RaccoonEvents.FilterInteractionEvent()
        self.eventManager.dispatchEvent(e)

    def removeInactive(self, event=None):
        """ remove inactive filters"""
        if len(self.filters) ==0 : return
        rem = []
        for o in self.filters:
            if not o.isActive():
                o.pack_forget()
                rem.append(o)
        for o in rem:
            self.filters.remove(o)



    def destroy(self, obj, event=None):
        """ remove a filter from the filters db
            and destroy the widget
        """
        obj.pack_forget()
        self.filters.remove(obj)
        e = RaccoonEvents.FilterInteractionEvent()
        self.eventManager.dispatchEvent(e)


    def getvalues(self, event=None):
        """ return the dictionary of all filters and the mode"""
        settings = { 'mode' : self._mode_choices[ self.modeChoice.getvalue() ] ,
                'pattern': {} }
        for o in self.filters:
            if o.isActive():
                otype = o.getType()
                opatt = o.getPattern()
                wanted = o.wanted
                if not otype in settings['pattern'].keys():
                    settings['pattern'][otype] = []
                self.dprint("iteractFilt[%s]  = [%s][%s]" % (otype, opatt, wanted))
                settings['pattern'][otype].append((opatt,wanted))
        return settings

    def update(self, event=None):
        """ when updating, fire this"""
        self.countActive()
        self.update_cb()
