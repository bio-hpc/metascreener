########################################################################
#
# Date: Nov. 2001  Author: Michel Sanner, Daniel Stoffler
#
#       sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/NetworkEditor/ImageNodeEditor.py,v 1.2 2013/10/01 21:55:47 sanner Exp $
#
# $Id: ImageNodeEditor.py,v 1.2 2013/10/01 21:55:47 sanner Exp $
#
#  OBSOLETE
#

import os, Tkinter, Pmw, ImageTk
from NetworkEditor.Editor import ObjectEditor
from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser
from mglutil.util.packageFilePath import findFilePath
from mglutil.util.callback import CallbackFunction
ICONPATH = findFilePath('Icons', 'WarpIV')
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

class ImageNodeEditor(ObjectEditor):

    def __init__(self, node, master=None):
        self.node = node
        ObjectEditor.__init__(self, node, 'ImageNode', master)


    def nameEntryChange_cb(self, event=None):
        """apply the new name to the node and remember it has been modified"""
        name = self.nameTk.get()
        self.node.name = name
        self.node.redrawNode()
        

    def Apply(self, event=None):
        self.nameEntryChange_cb()
        self.Dismiss()


    def createForm(self, master):
        """Create standard editor form and add a Pmw Group for input ports,
one for output ports and a check button for viewing the source node's code.
"""
        ObjectEditor.createForm(self, master)

        frame = Tkinter.Frame(self.top)
        Tkinter.Label(frame, text="fill color ").grid(row=0, column=0,
                                                      sticky='ne')
        photo = ImageTk.PhotoImage(
            file=os.path.join(ICONPATH, 'colorChooser24.png'))
        cb = CallbackFunction(self.setColor, 'fillColor')
        b = Tkinter.Button(frame, command=cb, image=photo)
        b.photo = photo
        b.grid(row=0, column=1, sticky='ne')

        cb = CallbackFunction(self.setOpacity, 'fillColor')
        fillOpacityThumbwheel = ThumbWheel(
            frame,
            labCfg={'text':'Opac.', 'side':'left'},
            showLabel=1, width=40, height=14,
            min=.001, max=1., type=float, 
            value = self.node.nodeStyle.fillColor[3],
            callback = cb, continuous=True,
            oneTurn=1., wheelPad=0)
        fillOpacityThumbwheel.grid(row=0, column=2, sticky='ne')
        
        Tkinter.Label(frame, text="outline color ").grid(row=1, column=0,
                                                      sticky='ne')
        photo = ImageTk.PhotoImage(
            file=os.path.join(ICONPATH, 'colorChooser24.png'))
        cb = CallbackFunction(self.setColor, 'outlineColor')
        b = Tkinter.Button(frame, command=cb, image=photo)
        b.photo = photo
        b.grid(row=1, column=1, sticky='ne')

        cb = CallbackFunction(self.setOpacity, 'outlineColor')
        outlineOpacityThumbwheel = ThumbWheel(
            frame,
            labCfg={'text':'Opac.', 'side':'left'},
            showLabel=1, width=40, height=14,
            min=.001, max=1., type=float, 
            value = self.node.nodeStyle.fillColor[3],
            callback = cb, continuous=True,
            oneTurn=1., wheelPad=0)
        outlineOpacityThumbwheel.grid(row=1, column=2, sticky='ne')

        frame.pack()
        

    def setColor(self, what):
        def cb(color):
            self.node.nodeStyle.configure(**{what:color})
            self.node.redrawNode()
            self.currentNodeStyle = None

        cc = ColorChooser(immediate=1, commands=cb,
                          title='Node %s color'%what)
        cc.pack(expand=1, fill='both')
        

    def setOpacity(self, what, value):
        if what=='fillColor':
            self.node.nodeStyle.fillColor[3] = value
        elif what=='outlineColor':
            self.node.nodeStyle.outlineColor[3] = value
        
        self.node.redrawNode()
        self.currentNodeStyle = None


