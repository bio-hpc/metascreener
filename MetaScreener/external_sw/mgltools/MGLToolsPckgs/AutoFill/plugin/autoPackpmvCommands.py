# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 16:52:04 2012

###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Ludovic Autin, Mostafa Al-Alusi, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# AFGui.py Authors: Ludovic Autin with minor editing/enhancement from Graham Johnson
#
# Copyright: Graham Johnson ©2010
#
# This file "AFGui.py" is part of autoPACK, cellPACK, and AutoFill.
#
#    autoPACK is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    autoPACK is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with autoPACK (See "CopyingGNUGPL" in the installation.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
    
Name: 'autoPACK/cellPACK GUI'
@author: Ludovic Autin with design/editing/enhancement by Graham Johnson
"""
from AutoFill.AFGui import AFGui
from ViewerFramework.VFCommand import CommandGUI
from Pmv.mvCommand import MVCommand
class AutoPACKCommand(MVCommand):
    undoStack = []
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly
        self.apgui = None
        
    def onAddCmdToViewer(self):
        # this is done for sub classes to be able to change the undoCmdsString
        self.undoCmdsString = self.name
        
    def onRemoveObjectFromViewer(self, object):
        self.cleanup()
    
    def onAddObjectToViewer(self, object):
        self.cleanup()

    def doit(self, *args, **kw):
        #get the gui and display it
        vi = self.vf.GUI.VIEWER
        if self.apgui is None :
            self.apgui =AFGui(title="AFGui",master=vi)
            self.apgui.setup(vi=vi)
        self.apgui.display()
        
    def __call__(self, *args, **kw):
        """None <--- buildDNA(name,seq,**kw)
        \nnodes---TreeNodeSet holding the current selection
        \ncolors---list of rgb tuple.
        \ngeomsToColor---list of the name of geometries to color,default is 'all'
        """
        status = self.doitWrapper(*args, **kw)#apply( self.doitWrapper, (name, seq), kw)
        return status

    def guiCallback(self):
        status = self.doitWrapper()

autoPACKGUI = CommandGUI()
autoPACKGUI.addMenuCommand('menuRoot', 'Compute',
                            'autoPack')
                            
commandList = [
    {'name':'autoPACK', 'cmd':AutoPACKCommand(), 'gui':autoPACKGUI}, 
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
