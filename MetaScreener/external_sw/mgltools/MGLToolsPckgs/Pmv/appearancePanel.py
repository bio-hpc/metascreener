#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2012
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/Pmv/appearancePanel.py,v 1.4 2013/11/15 20:15:51 annao Exp $

#
# $Id: appearancePanel.py,v 1.4 2013/11/15 20:15:51 annao Exp $
#
import Pmw, ImageTk, Tkinter, os
from opengltk.OpenGL import GL

from mglutil.util.callback import CallbackFunction
from Pmv.moleculeViewer import ICONPATH
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

class GeomAppearanceWidget:

    def __init__(self, master, vf):
        self.master = master
        self.vf = vf

        self.geoms = None # will be a list of geoms
        self.allw = []

        self.tools = [
            { 'name':'points',
              'icon': 'point24.png',
              'tooltip': 'Draw points for %s polygons',
              'cursor': 'hand',
            },
            { 'name':'wire',
              'icon': 'wire24.png',
              'tooltip': 'Draw wires for %s polygons',
              'cursor': 'hand',
            },
            { 'name':'gouraud',
              'icon': 'smooth24.png',
              'tooltip': 'Draw Gouraud shaded polygons for %s polygons',
              'cursor': 'hand',
            },
            { 'name':'outlined',
              'icon': 'outline24.png',
              'tooltip': 'Draw Gouraud shaded polygons with outline for %s polygons',
              'cursor': 'hand',
            },
            ]

        self.createGUI(master)

        
    def enable(self):
        for w in self.allw:
            w.configure(state='normal')

    def disable(self):
        for w in self.allw:
            w.configure(state='disable')

            
    def setGeoms(self, geoms):
        self.geoms = geoms
        if len(geoms):
            self.enable()
        else:
            self.disable()
            

    def doit(self, mode, face='front'):
        geoms = self.geoms
        for geom in geoms:
            if mode=='points':
                if face=='front':
                    geom.Set(inheritFrontPolyMode=False,
                             frontPolyMode='point', outline=False)
                else:
                    geom.Set(inheritBackPolyMode=False,
                             backPolyMode='point', outline=False)
            elif mode=='wire':
                if face=='front':
                    geom.Set(inheritFrontPolyMode=False, frontPolyMode='line',
                             outline=False, polyFace=face)
                else:
                    geom.Set(inheritBackPolyMode=False, backPolyMode='line',
                             outline=False)

            elif mode=='gouraud':
                if face=='front':
                    geom.Set(inheritFrontPolyMode=False, frontPolyMode='fill',
                             inheritShading=False, shading='smooth',
                             outline=False)
                else:
                    geom.Set(inheritBackPolyMode=False, backPolyMode='fill',
                             inheritShading=False, shading='smooth',
                             outline=False)
                    
            elif mode=='outlined':
                if face=='front':
                    geom.Set(inheritFrontPolyMode=False, frontPolyMode='fill',
                             inheritShading=False, shading='smooth',
                             outline=True)
                else:
                    geom.Set(inheritBackPolyMode=False, backPolyMode='fill',
                             inheritShading=False, shading='smooth',
                             outline=True)

    def createGUI(self, master):
        self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)

        # create a group for each set of commands
        self.groupw = w = Pmw.Group(master,
                                    tag_text='Appearance Tools')
        parent = w.interior()
        w.pack(side='top', anchor='nw', padx=2, pady=2)

        ##
        ## rendering buttons
        ##
        self.buttons = []
        bnum = 0
        row = col = 0

        ##
        ## add check button to show/hide FRONT polygons
        var = self.frontPolv = Tkinter.IntVar()
        var.set(1)
        b = Tkinter.Checkbutton(
            parent, compound='left', text='F', variable=var,
            command=self.cull_cb, indicatoron=0,
            state='disable')
        b.grid(row=row, column=col, sticky='ne')
        self.balloon.bind(b, 'Check to show front facing polygons')
        self.allw.append(b)

        col += 1
        for cmdDict in self.tools:
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, cmdDict['icon']))

            cmd = CallbackFunction(self.doit, cmdDict['name'])
            b = Tkinter.Button(
                parent, compound='left', image=photo,
                command=cmd, state='disable')
            b.photo = photo
            b.grid(row=row, column=col, sticky='ne')
            self.allw.append(b)
            self.buttons.append(b)
            self.balloon.bind(b, cmdDict['tooltip']%'front')

            # add line width control on right click
            if cmdDict['name']=='points':
                b.bind('<ButtonPress-3>', self.postPWCounter)

            # add line width control on right click
            if cmdDict['name']=='wire':
                b.bind('<ButtonPress-3>', self.postLWCounter)

            # add outline parameter panel on right click
            if cmdDict['name']=='outlined':
                b.bind('<ButtonPress-3>', self.postOutlineParamPanel)

            bnum += 1
            col += 1

        ##
        ## Front color
        ##
        photo = ImageTk.PhotoImage(
            file=os.path.join(ICONPATH, 'colorChooser24.png'))
        b = Tkinter.Button(parent, command=self.setColor, image=photo,
                           state='disable')
        b.photo = photo
        b.grid(row=row, column=col, sticky='ne')
        self.allw.append(b)
        self.balloon.bind(b, 'Choose color for front polygons')

        ##
        ## add check button to show/hide BACK polygons
        row += 1
        col = 0
        var = self.backPolv = Tkinter.IntVar()
        var.set(0)
        b = Tkinter.Checkbutton(
            parent, compound='left', text='B', variable=var,
            command=self.cull_cb, indicatoron=0,
            state='disable')
        b.grid(row=row, column=col, sticky='ne')
        self.balloon.bind(b, 'Check to show back facing polygons')
        self.allw.append(b)

        col += 1
        for cmdDict in self.tools:
            photo = ImageTk.PhotoImage(
                file=os.path.join(ICONPATH, cmdDict['icon']))

            cmd = CallbackFunction(self.doit, cmdDict['name'], 'back')
            b = Tkinter.Button(
                parent, compound='left', image=photo, 
                command=cmd, state='disable')
            b.photo = photo
            b.grid(row=row, column=col, sticky='ne')
            self.allw.append(b)
            self.buttons.append(b)
            self.balloon.bind(b, cmdDict['tooltip']%'back')

            # add line width control on right click
            if cmdDict['name']=='points':
                b.bind('<ButtonPress-3>', self.postPWCounter)

            # add line width control on right click
            if cmdDict['name']=='wire':
                b.bind('<ButtonPress-3>', self.postLWCounter)

            bnum += 1
            col += 1

        ##
        ## Back color
        ##
        photo = ImageTk.PhotoImage(
            file=os.path.join(ICONPATH, 'colorChooser24.png'))
        b = Tkinter.Button(parent, command=self.setColorB, image=photo,
                           state='disable')
        b.photo = photo
        b.grid(row=row, column=col, sticky='ne')
        self.allw.append(b)
        self.balloon.bind(b, 'Choose color for back polygons')

        ##
        ## opacity
        ##
        row += 1
        col = 0

        self.opcaTW = ThumbWheel(
            parent, showLabel=1, width=70, height=16, type=float, value=1.,
            callback=self.setOpacity, continuous=True, oneTurn=1.,min=0.0,
            max=1.0, wheelPad=2, labCfg = {'text':'opac:', 'side':'left'})
        self.opcaTW.grid(row=row, column=col, columnspan=4, sticky='ne')
        self.balloon.bind(self.opcaTW, 'Set geometry opacity')


        self.enable()


    def cull_cb(self):
        cf = not self.frontPolv.get()
        cb = not self.backPolv.get()
        for geom in self.geoms:
            if cf and cb:
                geom.Set(culling='front_and_back')
            elif cf:
                geom.Set(culling='front')
            elif cb:
                geom.Set(culling='back')
            else:
                geom.Set(culling='none')
            geom.viewer.deleteOpenglList()
        geom.viewer.Redraw()
    ##
    ## outline paarameter panel popup
    ##
    def postOutlineParamPanel(self, event):
        vi = self.vf.GUI.VIEWER
        for geom in self.geoms:
            vi.GUI.outlineMeshProp_cb(geometry=geom)
        
    ##
    ## Line width popup
    ##
    def postLWCounter(self, event):
        self._tmproot = root = Tkinter.Toplevel()
        vi = self.vf.GUI.VIEWER
        #pick = vi.lastPick
        #if pick is None: return
        #geom = pick.hits.keys()[0]
        geom = self.geoms[0]
        
        self._oldValue = geom.lineWidth
        root.transient()
        root.geometry("+%d+%d"%root.winfo_pointerxy())
        root.overrideredirect(True)
        c = self._int = Pmw.Counter(
            root,
            labelpos = 'w', label_text = 'line Width',
            orient = 'horizontal', entry_width = 2,
            entryfield_value = geom.lineWidth,
            #entryfield_validate = {'validator' : 'integer',
            #                       'min' : 1, 'max' : 10},
            entryfield_validate = self._custom_validate,
            entryfield_command = self.returnCB,
            )
        c.grid(row=0, column=0)
        self._counter = c

        im = ImageTk.PhotoImage(file=os.path.join(ICONPATH,'ok20.png'))
        b = Tkinter.Button(root, image=im, command=self.returnCB)
        b.im = im
        b.grid(row=0, column=1)

        im = ImageTk.PhotoImage(file=os.path.join(ICONPATH,'cancel20.png'))
        b = Tkinter.Button(root, image=im, command=self.cancelCB)
        b.im = im
        b.grid(row=0, column=2)

    def _custom_validate(self, text):
        try:
            val = float(text)
            if val > 0.0:
                ok = True
            else:
                ok = False
        except:
            ok = False
        if ok:
            self.setLW(val)
            return 1
        else:
            return -1

    def cancelCB(self, event=None, ok=False):
        if ok is False:
            self.setLW(self._oldValue)
        if hasattr(self, '_tmproot'):
            self._tmproot.destroy()
            del self._tmproot
            del self._oldValue


    def returnCB(self, event=None):
        value = self._counter.get()
        self.setLW(value)
        self.cancelCB(event, ok=True)

        
    def setLW(self, val):
        for geom in self.geoms:
            geom.Set(inheritLineWidth=False, lineWidth=int(val))

    ##
    ## Point width popup
    ##
    def postPWCounter(self, event):
        self._tmproot = root = Tkinter.Toplevel()
        vi = self.vf.GUI.VIEWER

        geom = self.geoms[0]
        
        self._oldValue = geom.lineWidth
        root.transient()
        root.geometry("+%d+%d"%root.winfo_pointerxy())
        root.overrideredirect(True)
        c = self._int = Pmw.Counter(
            root,
            labelpos = 'w', label_text = 'Point Width',
            orient = 'horizontal', entry_width=2,
            entryfield_value = geom.pointWidth,
            entryfield_validate = self._custom_validate1,
            entryfield_command = self.returnCB1,
            )
        c.grid(row=0, column=0)
        self._counter = c

        im = ImageTk.PhotoImage(file=os.path.join(ICONPATH,'ok20.png'))
        b = Tkinter.Button(root, image=im, command=self.returnCB1)
        b.im = im
        b.grid(row=0, column=1)

        im = ImageTk.PhotoImage(file=os.path.join(ICONPATH,'cancel20.png'))
        b = Tkinter.Button(root, image=im, command=self.cancelCB1)
        b.im = im
        b.grid(row=0, column=2)

    def _custom_validate1(self, text):
        try:
            val = float(text)
            if val > 0.0:
                ok = True
            else:
                ok = False
        except:
            ok = False
        if ok:
            self.setPW(val)
            return 1
        else:
            return -1

    def cancelCB1(self, event=None, ok=False):
        if ok is False:
            self.setPW(self._oldValue)
        if hasattr(self, '_tmproot'):
            self._tmproot.destroy()
            del self._tmproot
            del self._oldValue


    def returnCB1(self, event=None):
        value = self._counter.get()
        self.setPW(value)
        self.cancelCB1(event, ok=True)

        
    def setPW(self, val):
        for geom in self.geoms:
            # setting outline to False forces the change
            geom.Set(inheritPointWidth=False, pointWidth=int(val), outline=False)


    def setColor(self):
        from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser
        #vi = self.vf.GUI.VIEWER
        #pick = vi.lastPick
        #if pick is None: return
        #geom = pick.hits.keys()[0]
        geoms = self.geoms

        def cb(color, geoms=geoms):
            for geom in geoms:
                geom.Set(inheritMaterial=False, materials=[color])
            self.setOpacity(self.opcaTW.get())
            
        cc = ColorChooser(title="Front Color Chooser", immediate=1, commands=cb)
        cc.pack(expand=1, fill='both')


    def setOpacity(self, val):
        for geom in self.geoms:
            geom.Set(opacity=val, inheritMaterial=False, transparent=True)


    def setColorB(self):
        from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser
        geoms = self.geoms

        def cb(color, geoms=geoms):
            for geom in geoms:
                geom.Set(inheritMaterial=False, materials=[color], polyFace='back')
            self.setOpacity(self.opcaTW.get())
            
        cc = ColorChooser(title="Back Color Chooser", immediate=1, commands=cb)
        cc.pack(expand=1, fill='both')


    def setOpacityB(self, val):
        for geom in self.geoms:
            geom.Set(opacity=val, inheritMaterial=False, transparent=True,
                     polyFace='back')
