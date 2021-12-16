########################################################################
#
# Date: 2014 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################
#
# $Header: /opt/cvs/DejaVu2/Qt/Viewer.py,v 1.1.1.1 2014/06/19 19:41:03 sanner Exp $
#
# $Id: Viewer.py,v 1.1.1.1 2014/06/19 19:41:03 sanner Exp $
#
import threading

from PySide import QtGui, QtCore

import DejaVu2
from DejaVu2.Qt.Camera import Camera
from DejaVu2.Viewer import ViewerBase


#class Viewer(QtGui.QDockWidget, ViewerBase):
#class Viewer(QtGui.QMainWindow, ViewerBase):
class Viewer(QtGui.QWidget, ViewerBase):

    def __init__(self, master=None, nogui=0, screenName=None,
                 guiMaster=None, classCamera=None, showViewerGUI=True,
                 autoRedraw=True, verbose=True, cnf={}, **kw):
	"""Viewer's constructor
"""
        if guiMaster is not None and master is None:
            master = self
            self.ownMaster = True

        #QtGui.QDockWidget.__init__(self, master)
        #QtGui.QMainWindow.__init__(self, master)
        #self.setWindowTitle('DejaVu2_Viewer_Qt')        
        QtGui.QWidget.__init__(self, master)

        #self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        #self.fileMenu.hide()

        #self.toolBar = self.addToolBar(self.tr("Focus"))

        self.redrawTimer = QtCore.QTimer()
        self.connect(self.redrawTimer, QtCore.SIGNAL("timeout()"),
                     self.ReallyRedraw)

        # string var used to decide what the trackball is moving
        self.Xform = 'Object'

        self.contourTk = False

        self.spinVar = DejaVu2.defaultSpinningMode
        self.spinCallBack = None

        # Decides if the call to enable GL_LIGHTNING will be considered 
        self.OverAllLightingIsOn = 1
        
        self.master = master

        # not sure about this but if it is not there I have 100x3 black box in upper left corner
        #mainLayout = QtGui.QGridLayout()
        #self.setLayout(mainLayout)

        ViewerBase.__init__(self, nogui=0, screenName=None,
                            guiMaster=None, classCamera=None, 
                            autoRedraw=True, verbose=True, cnf={}, **kw)

        #objects = QtGui.QDockWidget('ObjectTree', self)
        #from tree import ObjectTree
        #self.objTree = ObjectTree(self, parent=objects)
        #objects.setWidget(self.objTree)
        
        #from dashboard import Dashboard
        #self.objTree = Dashboard(parent=objects)
        #objects.setWidget(self.objTree)
        #mainLayout.addWidget(objects)
        
        #self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, objects)

        #mainLayout.addWidget(self.cameras[0].master)

        # create the material editor
        self.materialEditor = None
    ##     self.materialEditor = MaterialEditor(None, self)
    ##     self.materialEditor.dismissTk.grid_forget()
    ##     self.materialEditor.dismiss()

    ##     # register Object that have their own OpenGL context but need to have
    ##     # the same lighting model and lights
    ##     for l in self.lights:
    ##         l.applyTo = [self.materialEditor]

    ##     self.lightModel.applyTo = [self.materialEditor]
        
    ##     # create the ViewerGui
    ##     if showViewerGUI:
    ##         self.GUI = ViewerGUI(self, self.maxLights, self.maxClipP,
    ##                              nogui=nogui, master=guiMaster)

    ##         #self.GUI.CameraBackgroundColor = self.CurrentCameraBackgroundColor
    ##         #self.GUI.LightColor = self.CurrentLightColor
    ##         #self.GUI.ClipColor = self.CurrentClipColor
    ##         #self.GUI.ObjectFrontColor = self.CurrentObjectFrontColor
    ##         #self.GUI.ObjectBackColor = self.CurrentObjectBackColor
    ##         #self.GUI.LightModelColor = self.LMColor

    ##         self.GUI.addObject(self.rootObject, None)

    ##         self.GUI.bindResetButton( self.Reset_cb)
    ##         self.GUI.bindNormalizeButton( self.Normalize_cb)
    ##         self.GUI.bindCenterButton( self.Center_cb)
    ##         self.GUI.bindDeleteButton( self.Delete_cb)
    ## ##         self.GUI.Exit = self.__del__

            ## if nogui and isinstance(self.GUI.root, Tkinter.Toplevel):
            ##     self.GUI.withdraw()

        #self.GUI.addObject(self.pickVerticesSpheres, None)
        #self.GUI.showPickedVertex.set(self.showPickedVertex)

        if self.autoRedraw:
            self.pendingAutoRedrawID = self.redrawTimer.start(10)


    def postNextRedraw(self):
        if self.autoRedraw:
            if self.redrawTimer.isActive():
                self.redrawTimer.stop()
            self.redrawTimer.start(100)


    def startAutoRedraw(self):
        self.autoRedraw = True
        self.redrawTimer.start(100)


    def stopAutoRedraw(self):
        if self.redrawTimer.isActive():
            self.redrawTimer.stop()
        self.autoRedraw = False   


    def checkIfRedrawIsNeeded(self):
        if self.suspendRedraw:
            self.redrawTimer.start(1000)
            #print 'NO REDRAW SUSPEND'
            return False

        if not self.needsRedraw:
            self.redrawTimer.start(100)
            #print 'NO REDRAW no needs'
            return False
                    
        if threading.currentThread().getName()!='MainThread':
            print 'NO REDRAW not main thread'
            #self.redrawTimer.start(100)
            return False

        if self.autoRedraw and not self.redrawTimer.isActive():
            #print 'NO REDRAW no active timer'            
            return False
        return True
    

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(
            self, "Confirmation",
            "Are you sure you want to quit?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


    def AddCamera(self, master=None, screenName=None, classCamera=None,
                  stereo='none', num=None, cnf={}, **kw):
	"""Add one more camera to this viewer"""

        if num is None:
            num = len(self.cameras)

        if classCamera is None:
            classCamera = Camera
            name = 'camera '+str(num)
        else:
            name = classCamera.__name__+str(num)
            
        cameraOwnsMaster = False
	if not master:
            master = self.master
            cameraOwnsMaster = True
        #master = QtGui.QDockWidget('Camera%d'%(len(self.cameras)+1), self)
        #self.addDockWidget(QtCore.Qt.RightDockWidgetArea, master)
        
        kw['stereo'] = stereo
            
        c = classCamera(master, screenName, self, num, check=1, cnf=cnf, **kw)
        c.show()
        
        #master.setWidget(c)
        #self.setCentralWidget(master)

        #if hasattr(c.frame.master,"protocol"):
        #    c.frame.master.protocol("WM_DELETE_WINDOW",self.closeEvent)
        ## c.eventManager.AddCallback('<KeyPress>', self.modifierDown)
        ## c.eventManager.AddCallback('<KeyRelease>', self.modifierUp)
        ## c.eventManager.AddCallback('R', self.Reset_cb_arg)
        ## c.eventManager.AddCallback('r', self.Reset_cb_arg)
        ## c.eventManager.AddCallback('A', self.AutoDepthCue)
        ## c.eventManager.AddCallback('a', self.AutoDepthCue)
        ## c.eventManager.AddCallback('N', self.Normalize_cb_arg)
        ## c.eventManager.AddCallback('n', self.Normalize_cb_arg)
        ## c.eventManager.AddCallback('C', self.Center_cb_arg)
        ## c.eventManager.AddCallback('c', self.Center_cb_arg)
        ## c.eventManager.AddCallback('D', self.Depth_cb_arg)
        ## c.eventManager.AddCallback('d', self.Depth_cb_arg)
        ## c.eventManager.AddCallback('T', self.toggleTransformRootOnly)
        ## c.eventManager.AddCallback('t', self.toggleTransformRootOnly)
        ## c.eventManager.AddCallback('L', self.toggleOpenglLighting)
        ## c.eventManager.AddCallback('l', self.toggleOpenglLighting)
        ## c.eventManager.AddCallback('O', self.SSAO_cb_arg)
        ## c.eventManager.AddCallback('o', self.SSAO_cb_arg)    
        c.ownMaster = cameraOwnsMaster
        
        ## if self.GUI is not None:
        ##     self.GUI.bindModifersToTransformInfo(master)

	self.cameras.append( c )
	if len(self.cameras)==1:
	    self.currentCamera = c
            c.hasBeenCurrent = 1
	    #c.frame.config( background = "#900000" )

	# make the trackball transform the current object
        #if self.rootObject:
        #    self.BindTrackballToObject(self.rootObject)

        c.firstRedraw = True
        c.Activate()

	return c


    ## def AddObject(self, obj, parent=None, redraw=True, redo=True):
    ##     ViewerBase.AddObject(self, obj, parent=parent, redraw=redraw, redo=redo)
    ##     self.objTree.addObject(obj.parent, obj, obj.name, str(obj))

##     def _DeleteCamera(self, camera):
##         """Remove the given camera in the right order
## """
##         #print 'Viewer._DeleteCamera ', camera
##         # Check if this camera shareCTX with other camera.
##         if hasattr(camera, 'shareCTXWith'): 
##             while len(camera.shareCTXWith):
##                 cam = camera.shareCTXWith[0]
##                 self._DeleteCamera(cam)
##         camera.destroy()
##         if camera.ownMaster:
##             camera.frame.master.destroy()
##         else:
##             camera.frame.destroy()
##         self.cameras.remove(camera)
##         for c in self.cameras:
##             if hasattr(c, 'shareCTXWith'):
##                 c.shareCTXWith.remove(camera)

        
##     def DeleteCamera(self, camera):
##         """
##         Remove the given camera from the viewer and takes care
##         of the dpyList if camera is cameras[0]
##         """
## #        #delete NPR rendering toplevel
## #        if camera.imCanvastop:
## #            camera.imCanvastop.destroy()
## #            camera.imCanvas = None
## #            camera.imCanvas1 = None
## #            camera.imCanvas2 = None
## #            camera.imCanvas3 = None
            
##         # Remove the camera from the list of cameras associated to
##         # the viewer.
##         camIndex = self.cameras.index(camera)

##         # the current openGL context has been destroyed so
##         # the dpyList need to be destroyed only if the CTX is not
##         # shared by any other camera.
##         if camIndex == 0:
##             self.objectsNeedingRedo = {}
##             for g in self.rootObject.AllObjects():
##                 g.deleteOpenglList()
##                 self.objectsNeedingRedo[g] = None

##         self._DeleteCamera(camera)
##         # If this camera is the current camera
##         if self.currentCamera == camera:
##             if len(self.cameras) == 0:
##                 # There is no more cameras then set currentCamera to None
##                 self.currentCamera = None
##             else:
##                 # Set the current Camera to be the first camera of the list.
##                 self.currentCamera = self.cameras[0]
