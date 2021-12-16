# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 23:53:00 2012
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
# This file "displayPreFill.py" is part of autoPACK, cellPACK, and AutoFill.
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
Name: -
@author: Ludovic Autin with design/editing/enhancement by Graham Johnson
"""

# create a Viewer
from DejaVu import Viewer
vi = Viewer()
from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
from DejaVu.Cylinders import Cylinders
from DejaVu.Box import Box
from DejaVu.Points import Points
from DejaVu.glfLabels import GlfLabels
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Polylines import Polylines

#display fill box
fbb = Box('fillpBB', cornerPoints=bb, visible=1)
vi.AddObject(fbb)

# create master for cytoplasm compartment
orgaToMasterGeom = {}
g = Geom('cytoplasm', visible=0)
orgaToMasterGeom[0] = g
orgaToMasterGeom[h1] = g
vi.AddObject(g)
# create masters for ingredients
r =  h1.exteriorRecipe
if r :
    for ingr in r.ingredients:
        gi = Geom('%s %s'%(ingr.pdb, ingr.name))
        vi.AddObject(gi, parent=g)
        orgaToMasterGeom[ingr] = gi

# display organelle mesh
for orga in h1.organelles:
    # create master for organelle
    g = Geom('organelle_%d'%orga.number)
    vi.AddObject(g)
    gs = Geom('surface')
    vi.AddObject(gs, parent=g)
    gc = Geom('Matrix')
    vi.AddObject(gc, parent=g)
    orgaToMasterGeom[orga] = g
    orgaToMasterGeom[orga.number] = gs
    orgaToMasterGeom[-orga.number] = gc

    # create masters for ingredients
    r =  orga.surfaceRecipe
    if r :
        for ingr in r.ingredients:
            gi = Geom('%s %s'%(ingr.pdb, ingr.name))
            vi.AddObject(gi, parent=gs)
            orgaToMasterGeom[ingr] = gi
    r =  orga.innerRecipe
    if r :
        for ingr in r.ingredients:
            gi = Geom('%s %s'%(ingr.pdb, ingr.name))
            vi.AddObject(gi, parent=gc)
            orgaToMasterGeom[ingr] = gi

    tet = IndexedPolygons('surfaceMesh', vertices=orga.vertices,
                          faces=orga.faces, normals=orga.vnormals,
                          inheritFrontPolyMode=False,
                          frontPolyMode='line',
                          inheritCulling=0, culling='none',
                          inheritShading=0, shading='flat')
    vi.AddObject(tet, parent=g)

cp = vi.clipP[0]
vi.GUI.clipvar[0][0].set(1)
tet.AddClipPlane( cp, 1, False)

# display histo BB 
hbb = Box('histoVolBB', cornerPoints=h1.boundingBox)
vi.AddObject(hbb)

fpg = Points('notFreePoints')
vi.AddObject(fpg)

# display organelle surface normals
for orga in h1.organelles:
    verts = []
    for i, p in enumerate(o1.surfacePoints):
        pt = h1.masterGridPositions[p]
        norm = o1.surfacePointsNormals[p]
        verts.append( (pt, (pt[0]+norm[0]*10, pt[1]+norm[1]*10, pt[2]+norm[2]*10) ) )

    n = Polylines('normals', vertices=verts, visible=0)
    vi.AddObject(n, parent=orgaToMasterGeom[orga])

    if hasattr(o1, 'ogsurfacePoints'):
        # display off grid surface grid points
        verts = []
        labels = []
        for i,pt in enumerate(orga.ogsurfacePoints):
            verts.append( pt )
            labels.append("%d"%i)

        s = Points('OGsurfacePts', vertices=verts, materials=[[1,1,0]],
                   inheritMaterial=0, pointWidth=3, inheritPointWidth=0,
                   visible=0)
        vi.AddObject(s, parent=orgaToMasterGeom[orga])
        labDistg = GlfLabels('OGsurfacePtLab', vertices=verts, labels=labels,
                             visible=0)
        vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])


    # display surface grid points
    verts = []
    colors = [(1,0,0)]
    labels = []
    for ptInd in orga.surfacePoints:
        verts.append( h1.masterGridPositions[ptInd])
        labels.append("%d"%ptInd)
    s = Points('surfacePts', vertices=verts, materials=colors,
               inheritMaterial=0, pointWidth=4, inheritPointWidth=0,
               visible=0)
    vi.AddObject(s, parent=orgaToMasterGeom[orga])
    labDistg = GlfLabels('surfacePtLab', vertices=verts, labels=labels,
                         visible=0)
    vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])

    # display interior grid points
    verts = []
    labels = []
    for ptInd in orga.insidePoints:
        verts.append( h1.masterGridPositions[ptInd])
        labels.append("%d"%ptInd)

    s = Points('insidePts', vertices=verts, materials=[[0,1,0]],
               inheritMaterial=0, pointWidth=4, inheritPointWidth=0,
               visible=0)
    vi.AddObject(s, parent=orgaToMasterGeom[orga])

    labDistg = GlfLabels('insidePtLab', vertices=verts, labels=labels,
                         visible=0)
    vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])

vi.Reset_cb()
vi.Normalize_cb()
vi.Center_cb()
cam = vi.currentCamera
cam.master.master.geometry('%dx%d+%d+%d'%(400,400, 92, 73))
vi.update()
cam.fog.Set(enabled=1)

sph = Spheres('debugSph', inheritMaterial=False)
vi.AddObject(sph)
