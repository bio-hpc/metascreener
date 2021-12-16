# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 11:28:27 2011

@author: -
"""

#vrml for chimera
#use VRML primitive
#PMV _ self.writeVRML2('./test.wrl', log=1, cylinderQuality=-1, saveNormals=0, colorPerVertex=True, redraw=0, useProto=0, sphereQuality=-1)
if True :
    import sys
    sys.path.insert(0,"/Users/ludo/DEV/MGLTOOLS/mgl32/MGLToolsPckgs/PIL")
    sys.path.insert(0,"/Users/ludo/DEV/MGLTOOLS/mgl32/MGLToolsPckgs")
    import upy
    helperClass = upy.getHelperClass()   
    ViewerType=helperClass.host
    vi = None
    helper = helperClass()
om = chimera.openModels
o = om.open(f,type="VRML")
#or use PDB + BIOMT=> geom ? VRML align to the PDB?
