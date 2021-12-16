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
import Tkinter as tk
import tkMessageBox as tmb
import Pmw, tkFont, ImageTk
import DebugTools
import threading, Queue, time, sys, platform
from CADD.Raccoon2 import HelperFunctionsN3P as hf



class RaccoonDefaultWidget:
    """ base widget for defining all the common aestetic settings"""
    def __init__(self, parent=None, iconpath=None):
        if not parent == None:
            self.parent = parent
        else:
            self.parent = tk.Tk()

        if iconpath:
            self.iconpath = iconpath


        self.sysarch = platform.uname()[0]
        # BUG
        # this is a fix that's needed to parse multiple files selections
        # due to a bug in askopenfilenames ( http://bugs.python.org/issue5712 )
        t = tk.Tk()
        t.withdraw()
        self._listfixer = t.splitlist
        #self._listfixer = self.parent.splitlist
        # BUG
        if self.sysarch=='Windows':
            normsize = 8
            smallsize = 7
        else:
            normsize = 9
            smallsize = 8
        family = 'Arial'
        #family = 'Helvetica'
        self.FONT = tkFont.Font(family=family,size=normsize)
        self.FONTbold = tkFont.Font(family=family,size=normsize,weight="bold")
        self.FONTsmall = tkFont.Font(family=family,size=smallsize)
        if self.parent:
            self.parent.option_add( "*font", "Arial %s bold" % normsize)
            self.parent.option_add( "*font", "Arial %s" % normsize) 
        #self.parent.option_add('*Background', '#969b9d')
        self.BORDER = { 'bd':1,'highlightbackground':'black',
                    'borderwidth':2,'highlightcolor':'black','highlightthickness':1}

class TabBase(DebugTools.DebugObj):
    def __init__(self, app, parent, debug = False):
        """ app         is the calling application
            parent      is the container where widgets will be created (
        """
        DebugTools.DebugObj.__init__(self, debug)
        self.app = app
        self.parent = parent
        self.frame = tk.Frame(parent)

    def resetFrame(self):
        self.frame.pack_forget()
        self.frame = tk.Frame(self.parent)



class PanedManager(RaccoonDefaultWidget):
    """
    """
    def __init__(self, app=None, parent=None, wtitle='PanedManager', ltitle='Left', rtitle='Right',
        lwidth=0, rwidth=0):
        RaccoonDefaultWidget.__init__(self, parent)
        self.app = app
        self.wtitle = wtitle
        self.ltitle = ltitle
        self.rtitle = rtitle
        self.lwidth = lwidth
        self.rwidth = rwidth

        self.initIcons()
        self.makeWin()


    def __call__(self): #, geom='centerscreenalways'):
        self.win.activate() #geometry=geom)

    def destroy(self, event=None):
        """
        """
        # trigger the event refresh of server list
        self.win.deactivate()

    def makeWin(self):
        """ """
        self.win = Pmw.Dialog(self.parent, title=self.wtitle, 
            buttons = ('Close',), command = self.destroy)

        bbox = self.win.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)
            #bbox.button(i).configure(relief='raised')

        self.pane = Pmw.PanedWidget(self.win.interior(), orient='horizontal', handlesize=-1,
            separatorthickness=10, separatorrelief='raised', )


        left = self.pane.add('info', min=self.lwidth, size=self.lwidth)
        right =  self.pane.add('viewer', min=self.rwidth, size=self.rwidth)
        handle = self.pane.component('handle-1')
        sep = self.pane.component('separator-1')

        self.pane.component('handle-1').place_forget()
        self.pane.component('handle-1').forget()
        self.pane.component('handle-1').pack_forget()
        self.pane.component('handle-1').grid_forget()
        self.pane.component('separator-1').configure(bd =2, #bg = '#999999'
            highlightthickness=1, highlightbackground='black', highlightcolor='black')
        lgroup = Pmw.Group(left, tag_text=self.ltitle, tag_font=self.FONTbold)
        lgroup.pack(expand=1,fill='both',side='top', anchor='center', padx=5,pady=5)
        self.left = lgroup.interior()

        rgroup = Pmw.Group(right, tag_text=self.rtitle, tag_font=self.FONTbold)
        rgroup.pack(expand=1,fill='both',side='left', anchor='center', padx=5,pady=5)
        self.right = rgroup.interior()

        # separator for rearranging 
        spacer = tk.Frame(self.right, width=6)
        spacer.pack(expand=0, fill='y',side='left', anchor='w')


        # nail handle
        tk.Frame(sep,height=40,width=4,bg='#fffeee',relief='sunken',bd=1,highlightbackground='black',
            highlightthickness=1).pack( anchor='center', padx=2,pady=2,side='left',expand=0,fill=None)

        # LEFT
        self.listcontainer = Pmw.ScrolledListBox(parent = self.left)
        self.listcontainer.component('listbox').configure(bg='white', font=self.FONT)
        self.listcontainer.pack(expand=1, fill='both')

        # RIGHT
        # pack everything
        self.pane.pack(expand=1,fill='both')

        self.pane.component('hull').configure(width=800, height=400)
    



class RacMenu(RaccoonDefaultWidget):
    """ Provide a self-destructible one-level pop-up menu
        (similar to what's usually associated to right-button 
        mouse clicks) and save expensive time-machine
        bills for getting back to the '80 to get 
        'Dismiss' buttons supplies.

        parent  : the parent widget (usually a button)
        items   : a nested list

             items = [ ['title'],                      <- only one entry : title (separator automatically added)
                                                                           [optional, leave empty entry for nothing]
        
                       ['entry', 'status', callback],  <- thre entries   : menu entries (text, normal/disabled, function)
                       [],                             <- empty          : separator
                       ['entry', 'status', callback],  <- thre entries   : menu entries (text, normal/disabled, function)
                       ['entry', 'status', callback],  <- thre entries   : menu entries (text, normal/disabled, function)
                     ]
        toolbar : optional, is usually a frame that contain the parent widget and 
                  other widgets; it is used to keep track of multiple menus in the same tooblar
        placement: close, under, tuple(x,y)... (others don't work yet)
        floating : it is not tied to a specific widget (i.e. button toolbar)

    """
    def __init__(self, parent, items=[], toolbar=False, placement='close', floating=False):
        RaccoonDefaultWidget.__init__(self, parent)
        self.menu = tk.Menu(parent, tearoff=False, takefocus=1)
        if not hasattr(self.parent, 'menu'):
            self.parent.menu = None
        self.items = items
        self._count = 0
        self._maxlen = 0
        self._posted = False
        self._caller = None
        self.floating = floating
        if toolbar:
            self.toolbar = toolbar
            self.toolbar.menu = None
        else:
            self.toolbar = False
        self.placement = placement
        self.parent.configure(relief='raised')
        self.populate()

    def populate(self):
        """ parse items and fill the menu """
        self.parent.configure(relief='raised')
        for i in range(len(self.items)):
            entry = self.items[i]
            if i == 0:              # LABEL
                if not entry == None:
                    self._count += 2
                    self.menu.add_command(label=entry[0], state='disable', 
                            font=self.FONTbold, foreground='white', background='black' )
                    self._maxlen = max( self._maxlen, len(entry[0]))
                    self.menu.add_separator()
            else:
                if len(entry) == 0: # SEPARATOR
                    self._count += 1
                    self.menu.add_separator()
                else:               # MENU ENTRY
                    self._count += 1
                    self._maxlen = max( self._maxlen, len(entry[0]))
                    l, s, c = entry
                    self.menu.add_command(label = ' '+ l +'  ',
                                          state= s,
                                          command = c,
                                          font = self.FONT)
        self.parent.configure(relief='raised')
        if not self.floating:
            self.parent.bind('<Button-1>', self)
            self.parent.bind('<Leave>', self._gozer)
            self.parent.bind('<FocusOut>', self._gozer)
        self.menu.configure(disabledforeground='white')
        self.menu.bind('<Leave>', self._gozer)
        self.menu.bind('<FocusOut>', self._gozer)
                
    def __call__(self, event=None):
        """ post the menu visible
        
            REMEMBER that all arrangements must not have discontinuities between
            the posted menu and the parent, otherwise a '<leave>' event would
            be triggered, calling _gozer)
        """
        self.parent.configure(relief='raised')
        if self._posted:
            self._gozer(force=True)
        if self.toolbar:
            # check if the toolbar doesn't have other
            # menu's posted
            if hasattr(self.toolbar, 'menu'):
                if self.toolbar.menu:
                    self.toolbar.menu._gozer(force=True)
        if self.placement == 'close':
            # NOTE the placement do not allow gaps! (otherwise they
            #      will trigger the <leave> event!)
            x = self.parent.winfo_rootx() + self.parent.winfo_width()# +1
            y = self.parent.winfo_rooty()

            self.menu.post(x, y)
            self.menu.bind('<Leave>', self._gozer)
            self._posted = True
            self.parent.menu = self
            if self.toolbar:
                self.toolbar.menu = self
            return

        elif self.placement == 'under':
            x = self.parent.winfo_rootx() #+ self.parent.winfo_width()# +1
            y = self.parent.winfo_rooty() + self.parent.winfo_height()
            self.menu.post(x, y)
            self.menu.bind('<Leave>', self._gozer)
            self._posted = True
            self.parent.menu = self
            if self.toolbar:
                self.toolbar.menu = self
            return            


        elif isinstance(self.placement, tuple):
            x, y = self.placement
            self.menu.post(x, y)
            self.menu.bind('<Leave>', self._gozer)
            self._posted = True
            self.parent.menu = self
            if self.toolbar:
                self.toolbar.menu = self
            self.menu.bind('<Leave>', self._gozer)
            self.menu.bind('<FocusOut>', self._gozer)
            return

        elif self.placement == 'left':
            x_off = -self._maxlen * 10
            y_off = -8
        elif self.placement == 'center':
            x_off = -self._maxlen * 5 # offset pixels per char
            y_off = -self.menu.yposition( self._count / 2)
        self._posted = True
        self.menu.post(event.x_root+x_off, event.y_root+y_off)


    def _gozer(self, event=None, force=False):
        """the Gozerian, the Destructor"""
        self.parent.configure(relief='raised')
        if force:
            self.menu.unpost()
            self._posted = False
            self.parent.menu = None
            return
        if not self._posted: return
        ex, ey = event.x_root, event.y_root

        mx0, my0 = self.menu.winfo_rootx(), self.menu.winfo_rooty()
        mw, mh = self.menu.winfo_width(), self.menu.winfo_height()
        mx1, my1 = mx0+mw, my0+mh

        px0, py0 = self.parent.winfo_rootx(), self.parent.winfo_rooty()
        pw, ph = self.parent.winfo_width(), self.parent.winfo_height()
        px1, py1 = px0+pw, py0+ph
        
        in_menu = False
        if mx0 <= ex < mx1:
            if my0 <= ey < my1:
                in_menu = True
        in_butt = False
        if not self.floating:
            if px0 <= ex < px1 :
                if py0 <= ey <= py1:
                    in_butt = True
        if in_butt or in_menu:
            return
        self._posted = False
        self.parent.menu = None
        if self.toolbar:
            self.toolbar.menu = None
        self.menu.unpost()

    def _gozer__BETTER_BUT_OFF(self, event=None, force=True):
        """the Gozerian, the Destructor"""
        # mouse coords
        x, y = event.x_root, event.y_root

        # calling button coords
        bx, by = self.parent.winfo_rootx(), self.parent.winfo_rooty()
        bw, bh = self.parent.winfo_width(), self.parent.winfo_width()

        # menu button coords
        mx, my = self.menu.winfo_rootx(), self.menu.winfo_rooty()
        mw, mh = self.menu.winfo_width(), self.menu.winfo_height()

        in_menu = ((x>mx)and(x<mx+mw)) and ((y>my)and(y< my+mh))
        in_button = ((x>bx)and(x<bx+bw)) and ((y>by)and(y< by+bh))
        print "\n\n\nIN MENU", in_menu
        print "IN BUTTON", in_button
        if in_menu:
            print "INMENU< RETURNING"
            return
        if in_button:
            print "INBUTTION< RETURNONG"
            return
        self._posted = False
        self.menu.unpost()



        """    
            


        if event.widget.winfo_containing(event.x, event.y) == self.menu:
            return
        event = None
        if event: 
            #print "EVENT", event,
            event.widget.unpost()
            self._posted = False
        else:
            self._posted = False
            self.menu.unpost()
        """

    """
    NOT ENOUGH TIME TO EXPERIMENT
    def __call__(self, event=None):
        "" post the menu visible""
        if self._posted:
            return
        #center = self.menu.yposition( self._count / 2)

        # use .configure(postcommand = self._gozer?)

        w = event.widget

        if self.placement == 'center':
            x = w.winfo_rootx()
            y = w.winfo_rooty() - self.menu.yposition( int(self._count / 2.))
        elif self.placement == 'n':
            x = w.winfo_rootx()
            y = w.winfo_rooty() - self.menu.yposition(self._count)            
        elif self.placement == 'ne':
            x = w.winfo_rootx() + w.winfo_width()/2
            y = w.winfo_rooty() - self.menu.yposition( int(self._count / 2.))
        elif self.placement == 's':
            x = w.winfo_rootx()
            y = w.winfo_rooty() - self.menu.yposition(self._count)            
        elif self.placement == 'close':
            x = 3
            y = -3
            self.menu.post(event.x_root+x, event.y_root+y)
        elif self.placement == 'right':
            #x_off = event.widget.1
            pass
            
        self._posted = True
        self.menu.after(50, lambda: self.menu.bind('<Leave>', self._gozer) )
        self.menu.post(x, y)

        """



class ProgressDialogWindow(RaccoonDefaultWidget , DebugTools.DebugObj):
    """ 
        parent          : Tk parent of the widget

        function        : function to be threaded

        func_args       : function arguments 

        func_kwargs     : function kw arguments 

        title           : title of the window

        message         : message to be shown in the window (LABEL)

        operation       : string with the description of the operation threaded
                          (used for the notification message text)

        image           : an ImageTk object ( or a file?) FIXME

        autoclose       : automatically close the dialog when threaded function 
                          successfully terminated

        cb              : callback passed to the threaded function, i.e. to perform updates

        progresstype    : description of the progress, that can be False (disabled) or
                          'percent' (return float percent) or 'count' (return integer)

        showtime        : Bool, show elapsed time
    
        debug           : enable debug

        USAGE: 

            the only requirement is that the function that is called should support
            as a parameter 'stopcheck' a function that returns True when the threaded
            function should stop (see self.start() )

                func_kwargs = {'path': "/", 'pattern': '*', 'recursive' : True}
                func = hf.pathToList
                progressWin = ProgressDialogWindow(parent, title, func, func_kwargs)
                progressWin.start()

    """
    def __init__(self, parent, function, func_args=(), func_kwargs={}, 
            title='ProgressDialogWindow', message='threaded operation', 
            operation = 'GenericProcessing', image = None, autoclose=False,
            cb = None, progresstype = None, showtime = True, debug=False):
        RaccoonDefaultWidget.__init__(self, parent)
        DebugTools.DebugObj.__init__(self, debug)
        self.title = title
        self._function = function
        self._args = func_args
        self._kwargs = func_kwargs
        self.image = image 
        self.message = message
        self.operation = operation
        self.autoclose = autoclose
        self.progresstype = progresstype
        self.showtime = showtime
        self.cb = cb
        self.queue = Queue.Queue()
        self.progress = 0
        self.pending = None
        self.status = 'not ready'
        self._STOP = False
        self._COMPLETED = False
        self._ERROR = None
        self._SLEEP = 0.1 # 075 # update interval (sec.)
        self.rolling = """-\|/""" # .oO@*  """
        #self.rolling = ".oO@*   "


    def stop(self, event=None):
        """ halt the thread"""
        t = 'Confirm'
        i = 'warning'
        m = 'Stop %s?' % self.operation
        if not tmb.askyesno(parent=self.win.interior(), title=t, icon=i, message=m):
            return
        self._STOP = True
        self._COMPLETED = False
        self.closingProcedure()
    
    def changeButton(self, event=None):
        """ update the text of the button when the thread ends/get stopped"""
        self.win.component('buttonbox').button(0).configure(text='Close', command=self.close)

    def getOutput(self):
        """return the output of the threaded function """
        if self.queue.empty():
            return []
        if self._ERROR:
            return []
        output = self.queue.get()
        return output

    def checkStop(self):
        """ function used to check if the thread must stop"""
        return self._STOP

    def close(self, event=None):
        """close the window"""
        self.win.destroy()


    def buildGUI(self):
        """ set the widgets shown"""
        self.win = Pmw.Dialog(self.parent, title=self.title, buttons=('Stop',), command=self.stop) 
        self.win.component('buttonbox').button(0).configure(font=self.FONT, default='disabled', **self.BORDER)
        #            TITLE
        # MESSAGE
        # Status : [ Running, stopped, error
        # Error:  xxxxxxxxxxxxx
        # Elapsed: 
        # Progress/process
        i = tk.Frame(self.win.interior(), relief = 'flat') #, bd=2) #, bg='white')
        # message
        f = tk.Frame(i) # , bg='white')
        if self.image:
            tk.Label(f, image = self.image).pack(anchor='w', side='left', expand=0, padx=6, pady=6)
        tk.Label(f, text = self.message, font=self.FONT).pack(anchor='w',side='left', expand=0, fill='x')
        f.pack(side='top', anchor='w', expand=0, fill='x',pady=5,padx=3)
        # status
        i.pack(expand=0,fill='both')

        i = tk.Frame(self.win.interior(), relief = 'sunken', bd=2, bg='white')
        # SPACER
        #tk.Frame(i, height=2, bd=2, relief='sunken',bg='black').pack(anchor='n', side='top', expand=0,fill='x')
        f = tk.Frame(i, bg='white')

        tk.Label(f, text = 'Status : ', width = 20, anchor='e',bg='white',
            font=self.FONTbold).pack(anchor='w',side='left', expand=0, fill='x')
        self.status_label = tk.Label(f, width = 30, text = 'ready', anchor='w', bg='white', font=self.FONT)
        self.status_label.pack(anchor='w',side='left', expand=0, fill='x')
        f.pack(side='top', anchor='w', expand=0, fill='x', padx=3)
        # elapsed time
        if self.showtime:
            f = tk.Frame(i, bg='white')
            tk.Label(f, text = 'Elapsed time : ', width = 20, anchor='e', bg='white',
                font=self.FONTbold).pack(anchor='w',side='left', expand=0, fill='x')
            self.time_label = tk.Label(f, width = 30, text = '00 : 00 : 00', anchor='w', 
                bg='white', font=self.FONT)
            self.time_label.pack(anchor='w',side='left', expand=0, fill='x')
            f.pack(side='top', anchor='w', expand=0, fill='x', padx=3)
        # error
        f = tk.Frame(i)
        self.error_title = tk.Label(f, text = ' ', fg='red', bg='white', width = 20, anchor='e', font=self.FONTbold)
        self.error_title.pack(anchor='w',side='left', expand=0, fill='x')
        self.error_label = tk.Label(f, width = 30, text = ' ', font=self.FONT, anchor='w', bg='white')
        self.error_label.pack(anchor='w',side='top', expand=0, fill='x')
        f.pack(side='top', anchor='w', expand=0, fill='x',padx=3)

        if self.progresstype == 'percent':
            #create percent bar
            f = tk.Frame(i, bg='white')
            self.progressBar = hf.ProgressBarThreadsafe(i, w = 300, h = 20)
            self.progressBar.pack(anchor='n', side='top', expand=0, fill='none')
            f.pack(side='top', anchor='n', expand=0, fill='none', padx=5, pady=8)
        elif self.progresstype == 'count':
            # create counter label
            # FIXME
            pass
        elif self.progresstype == None:
            # create the default "is alive" feedback
            self.dotsLabel = tk.Label(i, bg='white', text = self.rolling[0])
            self.dotsLabel.pack()
            pass
        i.pack(expand=0,fill='both')

    def setPercent(self, value):
        """update the percentage widget"""
        self.progress = value


    def _wrapped_function(self):
        """ the wrapped version of the function to be threaded
            with the FIFO queue used to export results
        """
        try:
        #if True:
            self._kwargs['stopcheck'] = self.checkStop
            if self.progresstype == 'percent':
                self._kwargs['showpercent'] = self.setPercent
            elif self.progresstype == 'count':
                #self._kwargs['showcount'] = self.setPercent
                pass
            res = self._function( *self._args, **self._kwargs)
            self.queue.put(res)
        except:
        #else:
            self._ERROR = sys.exc_info()[1]

    def start(self): 
        """ show the widget and start the threaded function 
        """
        self.buildGUI()
        # trigger the actual start...
        self.win.after(200, self._run)
        self.win.activate()
        
    def _run(self): 
        """ start the calculation and perform the GUI update"""
        self.status_label.configure(text = 'running')
        # create the thread and start it
        self.pending = threading.Thread(target = self._wrapped_function)
        self.pending.start()
        self.updateStatus()
        self._start_time = time.time()
        while self.status == 'running':
            time.sleep(self._SLEEP)
            self.updateStatus()
            self.updateGUI()
            self.updateGUI()

    def updateStatus(self):
        """ return the status of the job"""
        if self.pending == None:
            self.status = 'not started'
        elif self.pending.isAlive():
            self.status = 'running'
        elif not self._STOP:
            self._COMPLETED = True
            self.status = 'completed'
            self.closingProcedure()
        elif self._STOP:
            self.COMPLETED = False
            self.status = 'stopped'
            self.closingProcedure()

    def updateGUI(self):
        """ update the progress status"""
        try:
            self.parent.update()
            if self.showtime:
                # update time
                s = int(time.time() - self._start_time)
                h = s/3600
                remainder = s % 3600
                m = remainder/60
                s = remainder % 60
                timestr = "%02d : %02d : %02d" % (h,m,s)
                self.time_label.configure(text = timestr)
            if self.progresstype == 'percent':
                self.progressBar.set(self.progress)
                return
            elif self.progresstype == 'count':
                # update counter # FIXME
                return
            # provide the generic progress
            self.rolling = self.rolling[1:] + self.rolling[0]
            self.dotsLabel.configure(text = self.rolling[0])
        except tk.TclError:
            # possibly a latest update that was late
            pass
        except:
            print "[ unexpected error in RaccoonBasics, not dangerous... possibly...]"
            pass


    def closingProcedure(self):
        """ perform gui closing procedure when
            the threaded operation is completed
        """

        if not self._ERROR == None:
            # enable the error field
            self.error_title.configure(text='Error : ')
            self.error_label.configure(text=self._ERROR)
            status = 'error'
        
        elif self._COMPLETED:
            if self.autoclose and not self._ERROR:
                self.close()
                return
            status = 'done'
        elif self._STOP:
            status = 'stopped'

        self.status_label.configure(text = status)
        if self.progresstype == None:
            self.dotsLabel.configure(text='  ')
        self.changeButton()



       

class ProgressDialogWindowTk(RaccoonDefaultWidget , DebugTools.DebugObj):
    """ 
        parent          : Tk parent of the widget

        function        : function to be threaded

        func_args       : function arguments 

        func_kwargs     : function kw arguments 

        title           : title of the window

        message         : message to be shown in the window (LABEL)

        operation       : string with the description of the operation threaded
                          (used for the notification message text)

        image           : an ImageTk object ( or a file?) FIXME

        autoclose       : automatically close the dialog when threaded function 
                          successfully terminated

        cb              : callback passed to the threaded function, i.e. to perform updates

        progresstype    : description of the progress, that can be False (disabled) or
                          'percent' (return float percent) or 'count' (return integer)

        showtime        : Bool, show elapsed time
    
        debug           : enable debug

        USAGE: 

            the only requirement is that the function that is called should support
            as a parameter 'stopcheck' a function that returns True when the threaded
            function should stop (see self.start() )

                func_kwargs = {'path': "/", 'pattern': '*', 'recursive' : True}
                func = hf.pathToList
                progressWin = ProgressDialogWindow(parent, title, func, func_kwargs)
                progressWin.start()

    """
    def __init__(self, parent, function, func_args=(), func_kwargs={}, 
            title='ProgressDialogWindow', message='threaded operation', 
            operation = 'GenericProcessing', image = None, autoclose=False,
            cb = None, progresstype = None, showtime = True, debug=False):
        RaccoonDefaultWidget.__init__(self, parent)
        DebugTools.DebugObj.__init__(self, debug)
        self.title = title
        self._function = function
        self._args = func_args
        self._kwargs = func_kwargs
        self.image = image 
        self.message = message
        self.operation = operation
        self.autoclose = autoclose
        self.progresstype = progresstype
        self.showtime = showtime
        self.cb = cb
        self.status = 'not ready'
        self.result = None
        self._STOP = False
        self._COMPLETED = False
        self._ERROR = None
        self._SLEEP = 0.1 # 075 # update interval (sec.)
        self.rolling = """-\|/""" # .oO@*  """
        self.rolling_counter = 0
        self.rolling = unicode(u"\u2588\u2589\u258A\u258B\u258C\u258D\u258E\u258F") # horizontal
        #self.rolling = unicode(u"\u2581\u2582\u2583\u2584\u2585\u2586\u2587") # vertical
        #self.rolling = ".oO@*   "


    def stop(self, event=None):
        """ halt the thread"""
        t = 'Confirm'
        i = 'warning'
        m = 'Stop %s?' % self.operation
        if not tmb.askyesno(parent=self.win.interior(), title=t, icon=i, message=m):
            return
        self._STOP = True
        self._COMPLETED = False
        self.closingProcedure()
    
    def changeButton(self, event=None):
        """ update the text of the button when the thread ends/get stopped"""
        self.win.component('buttonbox').button(0).configure(text='Close', command=self.close)

    def getOutput(self):
        """return the output of the threaded function """
        #if self.queue.empty():
        #    return []
        #if self._ERROR:
        #    return []
        #output = self.queue.get()
        return self.result

    def checkStop(self):
        """ function used to check if the thread must stop"""
        return self._STOP

    def close(self, event=None):
        """close the window"""
        self.win.destroy()


    def buildGUI(self):
        """ set the widgets shown"""
        self.win = Pmw.Dialog(self.parent, title=self.title, buttons=('Stop',), command=self.stop) 
        button = self.win.component('buttonbox').button(0)
        button.configure(font=self.FONT, default='disabled', cursor='arrow', **self.BORDER)
        #            TITLE
        # MESSAGE
        # Status : [ Running, stopped, error
        # Error:  xxxxxxxxxxxxx
        # Elapsed: 
        # Progress/process
        i = tk.Frame(self.win.interior(), relief = 'flat') #, bd=2) #, bg='white')
        # message
        f = tk.Frame(i) # , bg='white')
        if self.image:
            tk.Label(f, image = self.image).pack(anchor='w', side='left', expand=0, padx=6, pady=6)
        tk.Label(f, text = self.message, font=self.FONT).pack(anchor='w',side='left', expand=0, fill='x')
        f.pack(side='top', anchor='w', expand=0, fill='x',pady=5,padx=3)
        # status
        i.pack(expand=0,fill='both')

        i = tk.Frame(self.win.interior(), relief = 'sunken', bd=2, bg='white')
        # SPACER
        f = tk.Frame(i, bg='white')
        tk.Label(f, text = 'Status : ', width = 20, anchor='e',bg='white',
            font=self.FONTbold).pack(anchor='w',side='left', expand=0, fill='x')
        self.status_label = tk.Label(f, width = 30, text = 'ready', anchor='w', bg='white', font=self.FONT)
        self.status_label.pack(anchor='w',side='left', expand=0, fill='x')
        f.pack(side='top', anchor='w', expand=0, fill='x', padx=3)
        # elapsed time
        if self.showtime:
            f = tk.Frame(i, bg='white')
            tk.Label(f, text = 'Elapsed time : ', width = 20, anchor='e', bg='white',
                font=self.FONTbold).pack(anchor='w',side='left', expand=0, fill='x')
            self.time_label = tk.Label(f, width = 30, text = '00 : 00 : 00', anchor='w', 
                bg='white', font=self.FONT)
            self.time_label.pack(anchor='w',side='left', expand=0, fill='x')
            f.pack(side='top', anchor='w', expand=0, fill='x', padx=3)
        # error
        f = tk.Frame(i)
        self.error_title = tk.Label(f, text = ' ', fg='red', bg='white', width = 20, anchor='e', font=self.FONTbold)
        self.error_title.pack(anchor='w',side='left', expand=0, fill='x')
        self.error_label = tk.Label(f, width = 30, text = ' ', font=self.FONT, anchor='w', bg='white')
        self.error_label.pack(anchor='w',side='top', expand=0, fill='x')
        f.pack(side='top', anchor='w', expand=0, fill='x',padx=3)

        if self.progresstype == 'percent':
            #create percent bar
            f = tk.Frame(i, bg='white')
            self.progressBar = hf.ProgressBarThreadsafe(i, w = 300, h = 20)
            self.progressBar.pack(anchor='n', side='top', expand=0, fill='none')
            f.pack(side='top', anchor='n', expand=0, fill='none', padx=5, pady=8)
        elif self.progresstype == 'count':
            # create counter label
            # FIXME
            pass
        elif self.progresstype == None:
            # create the default "is alive" feedback
            self.dotsLabel = tk.Label(i, bg='white', text = self.rolling[0])
            self.dotsLabel.pack()
            pass
        i.pack(expand=0,fill='both')

    def setPercent(self, value):
        """update the percentage widget"""
        self.progress = value

    def start(self):
        """ initiate the processing """
        # build the GUI
        self.buildGUI()
        # schedule the start function
        self.parent.after(100, self.run)
        # show gui
        self.win.activate()

    def getResults(self):
        """ set the complete variable to True"""
        return self.result

    def run(self,event=None):
        """ run the blocking function"""
        wrap_kwargs = { 'stopcheck' : self.checkStop,
                        'GUI'       : self.win.interior(),
                      }
        if self.progresstype == 'percent':
            wrap_kwargs['showpercent'] = self.progressBar.set
        self._kwargs.update(wrap_kwargs)
        self._start_time = time.time()
        # schedule an update
        self.win.interior().after(100, self.updateGUI )
        try:
            self.result = self._function(**self._kwargs)
            self._COMPLETED = True
        except:
            self._ERROR = sys.exc_info()[1]
            self._STOP = True
            print "CATCHED ERROR!", self._ERROR


    #XXX REDEFINE THE CLOSE PROTOCOL TO BE CLOSE()!!!!

    def updateGUI(self):
        """ update the progress status"""
        if self._COMPLETED or self._STOP:
            self.closingProcedure()
            return
        self.win.interior().after(100, self.updateGUI )
        if self.showtime:
            # update time
            s = int(time.time() - self._start_time)
            h = s/3600
            remainder = s % 3600
            m = remainder/60
            s = remainder % 60
            timestr = "%02d : %02d : %02d" % (h,m,s)
            self.time_label.configure(text = timestr)
        if self.progresstype:
            return
        #if self.progresstype == 'percent':
        #    self.progressBar.set(self.progress)
        #    return
        #elif self.progresstype == 'count':
        #    # update counter # FIXME
        #    return
        # provide the generic progress
        #if self.rolling_counter > len(self.rolling):
        #    self.rolling=self.rolling[::-1]
        #    self.rolling_counter = 0
        #    print "inverting"
        self.rolling = self.rolling[1:] + self.rolling[0]
        #string = " ".join(list(self.rolling[::-1]) )
        string = " ".join(list(self.rolling))
        self.dotsLabel.configure(text = string, fg='blue', bg='white') #, **self.BORDER) # [0])
        self.rolling_counter += 1


    def closingProcedure(self):
        """ perform gui closing procedure when
            the threaded operation is completed
        """

        testers = []
        if not self._ERROR == None:
            # enable the error field
            self.error_title.configure(text='Error : ')
            self.error_label.configure(text=self._ERROR)
            status = 'error'
        
        elif self._COMPLETED:
            if self.autoclose and not self._ERROR:
                self.close()
                return
            status = 'done'
        elif self._STOP:
            status = 'stopped'
        self.status_label.configure(text = status)
        if self.progresstype == None:
            self.dotsLabel.configure(text='  ')
        self.changeButton()


class About(RaccoonDefaultWidget):
    """ refined about window"""
    def __init__(self, parent=None, iconpath=None):
        RaccoonDefaultWidget.__init__(parent, iconpath)
        self.tabs = {}
        self.win = Pmw.Dialog(self.parent, title='About Raccoon2', buttons=('Close',))
        self.notebook = Pmw.NoteBook(self.parent)
        for tab in ['About', 'Funding & Acknowledgements']:
            self.tabs[tab] = self.notebook.add(tab)
        self.notebook.pack(expand=1, fill='both')
        self.notebook.setnaturalsize(self.tabs.keys())
        self.initImages()
        self.populateAbout()
        self.populateAuthors()
        self.populateFundingAck()
        self.win.activate()

    def initImages(self):
        """ initialize the icons for the interface"""
        images_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + '.png'
        self._ICON_sys = ImageTk.PhotoImage(Image.open(f))



    
    def populateAbout(self):
        """ about raccoon"""
        text = ('AutoDock | Raccoon 2\n'
                'v1.0beta rev 0.1\n')
        pass

    def populateAuthors(self):
        """ set authors names"""
        authors = ['Stefano Forli, TSRI', 
                   'Arthur J. Olson, TSRI', 
                   'Michel Sanner, TSRI']

    def populateFundingAck(self):
        thanks = ['Lisa Dong', 'Jc Ducomm',
                  'Alex L. Perryman',
                  'Luca',
                  'Peter']
        pass



