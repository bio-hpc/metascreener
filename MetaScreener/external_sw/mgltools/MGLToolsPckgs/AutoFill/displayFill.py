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
# This file "displayFill.py" is part of autoPACK, cellPACK, and AutoFill.
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

# display cytoplasm spheres
verts = {}
radii = {}
r =  h1.exteriorRecipe
if r :
    for ingr in r.ingredients:
        verts[ingr] = []
        radii[ingr] = []

for pos, rot, ingr, ptInd in h1.molecules:
    level = ingr.maxLevel
    px = ingr.transformPoints(pos, rot, ingr.positions[level])
    for ii in range(len(ingr.radii[level])):
        verts[ingr].append( px[ii] )
        radii[ingr].append( ingr.radii[level][ii] )

if r :
    for ingr in r.ingredients:
        if len(verts[ingr]):
            if ingr.modelType=='Spheres':
                sph = Spheres('spheres', inheritMaterial=0,
                              centers=verts[ingr], materials=[ingr.color],
                              radii=radii[ingr], visible=1)
                vi.AddObject(sph, parent=orgaToMasterGeom[ingr])
##             elif ingr.modelType=='Cylinders':
##                 cyl = Cylinders('Cylinders', inheritMaterial=0,
##                               vertices=verts[ingr], materials=[ingr.color],
##                               radii=radii[ingr], visible=1)
##                 vi.AddObject(cyl, parent=orgaToMasterGeom[ingr])


# display cytoplasm meshes
r =  h1.exteriorRecipe
if r :
    meshGeoms = {}
    for pos, rot, ingr, ptInd in h1.molecules:
        if ingr.mesh: # display mesh
            geom = ingr.mesh
            mat = rot.copy()
            mat[:3, 3] = pos
            if not meshGeoms.has_key(geom):
                meshGeoms[geom] = [mat]
                geom.Set(materials=[ingr.color], inheritMaterial=0, visible=0)
            else:
                meshGeoms[geom].append(mat)
                vi.AddObject(geom, parent=orgaToMasterGeom[ingr])

    for geom, mats in meshGeoms.items():
        geom.Set(instanceMatrices=mats, visible=1)

# display organelle spheres
for orga in h1.organelles:
    verts = {}
    radii = {}
    rs =  orga.surfaceRecipe
    if rs :
        for ingr in rs.ingredients:
            verts[ingr] = []
            radii[ingr] = []
    ri =  orga.innerRecipe
    if ri:
        for ingr in ri.ingredients:
            verts[ingr] = []
            radii[ingr] = []

    for pos, rot, ingr, ptInd in orga.molecules:
        level = ingr.maxLevel
        px = ingr.transformPoints(pos, rot, ingr.positions[level])
        if ingr.modelType=='Spheres':
            for ii in range(len(ingr.radii[level])):
                verts[ingr].append( px[ii] )
                radii[ingr].append( ingr.radii[level][ii] )
        elif ingr.modelType=='Cylinders':
            px2 = ingr.transformPoints(pos, rot, ingr.positions2[level])
            for ii in range(len(ingr.radii[level])):
                verts[ingr].append( px[ii] )
                verts[ingr].append( px2[ii] )
                radii[ingr].append( ingr.radii[level][ii] )
                radii[ingr].append( ingr.radii[level][ii] )

    if rs :
        for ingr in rs.ingredients:
            if len(verts[ingr]):
                if ingr.modelType=='Spheres':
                    sph = Spheres('spheres', inheritMaterial=False,
                                  centers=verts[ingr], radii=radii[ingr], 
                                  materials=[ingr.color], visible=0)
                    vi.AddObject(sph, parent=orgaToMasterGeom[ingr])
                elif ingr.modelType=='Cylinders':
                    v = numpy.array(verts[ingr])
                    f = numpy.arange(len(v))
                    f.shape=(-1,2)
                    cyl = Cylinders('Cylinders', inheritMaterial=0,
                                    vertices=v, faces=f, materials=[ingr.color],
                                    radii=radii[ingr], visible=1,
                                    inheritCulling=0, culling='None',
                                    inheritFrontPolyMode=0, frontPolyMode='line')
                    vi.AddObject(cyl, parent=orgaToMasterGeom[ingr])
                
    if ri:
        for ingr in ri.ingredients:
            if len(verts[ingr]):
                if ingr.modelType=='Spheres':
                    sph = Spheres('spheres', inheritMaterial=False,
                                  centers=verts[ingr], radii=radii[ingr], 
                                  materials=[ingr.color], visible=0)
                    vi.AddObject(sph, parent=orgaToMasterGeom[ingr])
                elif ingr.modelType=='Cylinders':
                    v = numpy.array(verts[ingr])
                    f = numpy.arange(len(v))
                    f.shape=(-1,2)
                    cyl = Cylinders('Cylinders', inheritMaterial=0,
                                    vertices=v, faces=f, materials=[ingr.color],
                                    radii=radii[ingr], visible=1,
                                    inheritCulling=0, culling='None',
                                    inheritFrontPolyMode=0, frontPolyMode='line')
                    vi.AddObject(cyl, parent=orgaToMasterGeom[ingr])


# display organelle meshes
for orga in h1.organelles:
    matrices = {}
    rs =  orga.surfaceRecipe
    if rs :
        for ingr in rs.ingredients:
            if ingr.mesh: # display mesh
                matrices[ingr] = []
                ingr.mesh.Set(materials=[ingr.color], inheritMaterial=0)
                
    ri =  orga.innerRecipe
    if ri :
        for ingr in ri.ingredients:
            if ingr.mesh: # display mesh
                matrices[ingr] = []
                ingr.mesh.Set(materials=[ingr.color], inheritMaterial=0)

    for pos, rot, ingr, ptInd in orga.molecules:
        if ingr.mesh: # display mesh
            geom = ingr.mesh
            mat = rot.copy()
            mat[:3, 3] = pos
            matrices[ingr].append(mat)
            vi.AddObject(geom, parent=orgaToMasterGeom[ingr])

    for ingr, mats in matrices.items():
        geom = ingr.mesh
        geom.Set(instanceMatrices=mats, visible=1)
        vi.AddObject(geom, parent=orgaToMasterGeom[ingr])


from DejaVu.colorTool import RGBRamp, Map
verts = []
labels = []
for i, value in enumerate(h1.distToClosestSurf):
    if h1.gridPtId[i]==1:
        verts.append( h1.masterGridPositions[i] )
        labels.append("%.2f"%value)
lab = GlfLabels('distanceLab', vertices=verts, labels=labels, visible=0)
vi.AddObject(lab)

# display grid points with positive distances left
verts = []
rads = []
for pt in h1.freePointsAfterFill[:h1.nbFreePointsAfterFill]:
    d = h1.distancesAfterFill[pt]
    if d>h1.smallestProteinSize-0.001:
        verts.append(h1.masterGridPositions[pt])
        rads.append(d)

if len(verts):
    sph1 = Spheres('unusedSph', centers=verts, radii=rads, inheritFrontPolyMode=0,
                   frontPolyMode='line', visible=0)
    vi.AddObject(sph1)

if len(verts):
    pts1 = Points('unusedPts', vertices=verts, inheritPointWidth=0,
                  pointWidth=4, inheritMaterial=0, materials=[(0,1,0)], visible=0)
    vi.AddObject(pts1)

verts = []
for pt in h1.freePointsAfterFill[:h1.nbFreePointsAfterFill]:
    verts.append(h1.masterGridPositions[pt])

unpts = Points('unused Grid Points', vertices=verts, inheritMaterial=0,
              materials=[green], visible=0)
vi.AddObject(unpts)

verts = []
for pt in h1.freePointsAfterFill[h1.nbFreePointsAfterFill:]:
    verts.append(h1.masterGridPositions[pt])

uspts = Points('used Grid Points', vertices=verts, inheritMaterial=0,
              materials=[red], visible=0)
vi.AddObject(uspts)

if hasattr(h1, 'jitter vectors'):
    from DejaVu.Polylines import Polylines
    verts = []
    for p1, p2 in (h1.jitterVectors):
        verts.append( (p1, p2))

    jv = Polylines('jitter vectors', vertices=verts, visible=1,
                   inheritLineWidth=0, lineWidth=4)
    vi.AddObject(jv, parent=orgaToMasterGeom[h1])


def dspMesh(geom):
    for c in geom.children:
        if c.name=='mesh':
            c.Set(visible=1)

def undspMesh(geom):
    for c in geom.children:
        if c.name=='mesh':
            c.Set(visible=0)

def dspSph(geom):
    for c in geom.children:
        if c.name=='spheres':
            c.Set(visible=1)

def undspSph(geom):
    for c in geom.children:
        if c.name=='spheres':
            c.Set(visible=0)


def showHide(func):
    r =  h1.exteriorRecipe
    if r :
        for ingr in r.ingredients:
            master = orgaToMasterGeom[ingr]
            func(master)
    for orga in h1.organelles:
        rs =  orga.surfaceRecipe
        if rs :
            for ingr in rs.ingredients:
                master = orgaToMasterGeom[ingr]
                func(master)
        ri =  orga.innerRecipe
        if ri:
            for ingr in ri.ingredients:
                master = orgaToMasterGeom[ingr]
                func(master)

showHide(dspMesh)
showHide(undspSph)
