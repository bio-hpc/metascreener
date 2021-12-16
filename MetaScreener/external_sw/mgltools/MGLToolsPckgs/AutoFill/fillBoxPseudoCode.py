# -*- coding: utf-8 -*-
"""
Created on Saturday September 1 1:50:00 2012
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
# This file "fillBoxPseudoCode.py" is part of autoPACK, cellPACK, and AutoFill.
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
@author: Graham Johnson
"""

# A lot of this can go in the setup scripts, but I think a lot can go into some generic script that gets called in the setup script.

##############################################################################################
# Collect any and all organelles including the new OrthoBoxOrganelle option described below  #
##############################################################################################

for i organelleMeshes in Recipe:
    o_i = Organelle(mesh_i)
    h1.addOrganelle(o_i)
    o_i.setSurfaceRecipe([o_iSurfaceRecipe])
    o_i.setInnerRecipe([o_iInnerRecipe])
exteriorBoundingBox = afviewer.helper.getObject("exteriorBoundingBox") # Currently called "histoVolBB", but would be good to rename now
fillSelectionObject = afviewer.helper.getOjbect("fillSelection") # Currently called "fillBB"
o_bb=None
if exteriorBoundingBox:
        # It will likely be very rare to have an exteriorBoundingBox, but useful for doing
        #  parallel processing, secondFills, PreviousFills, and artful intersections, so we need it.
    o_bb = Organelle(orthogonalBoxType=bool, "exteriorBoundingBox")
        # The bounding box is a "real" organelle
        #  and needs to be treated as one with
        #  special conditions (i.e., no surface and fast insidePt calculation shortcuts)
        #  All it does is allow limits to be set to exterior Recipe which
        #  is otherwise outwardly infinite
    o_bb.setExteriorRecipe([o_bbExteriorRecipe])
    h1.addOrganelle(o_bb)

masterGrid = None
if LoadGridFromFile:
    masterGrid = loadedGrid
    masterBB = masterGridBB

#else:
if fillSelectionObject == None:
    if masterGrid:
        fillSelectionObject = helper.cube.setCorners(organelles(masterBB))
    elif len(Organelles) > 0:
        fillSelectionObject = helper.cube.setCorners(organelles(getTotalSceneBoundingBox))
    else:
        fillSelectionObject = helper.cube.setCorners([-100,-100,-100],[100,100,100])
    #There is code for the boundingBox of a scene (walks through all organelle meshes to find max/min x,y,z points)
    # in HistoVol BuildGrids and Organelle, etc... its what we use for limits of old masterGrid code BB size.
padBest = largestProteinSize+JitterMax
if pad == None:
    pad = padBest
if pad == type(float) || if pad == type(int):
    if pad != padBest:
        afviewer.dialogBox("Your grid padding is inefficient. Do you want to override with the best setting?",[yes], [no]):
            yes: pad = padBest
if pad == type(vector):
    if pad != padBest:
        afviewer.dialogBox("Your grid padding is inefficient. Do you want to override with the best setting?",[yes], [no]):
            yes: pad = padBest
else:
    afviewer.dialogBox("Your padding is not recognized. Override with best setting or cancel?",[override], [cancel fill]):
        yes: pad = padBest
if pad != type(vector)
    pad = [pad,pad,pad]
if masterGrid:
    fillSelectionX0,fillSelectionY0,fillSelectionZ0 = fillSelectionObjectBB[0]-pad
    fillSelectionX1,fillSelectionY1,fillSelectionZ1 = fillSelectionObjectBB[1]+pad
    masterGridX0,masterGridY0,masterGridZ0 = masterGridBB[0]
    masterGridX1,masterGridY1,masterGridZ1 = masterGridBB[1]
    if fillSelectionX0<masterGridX0, or fillSelectionY0<masterGridY0, or fillSelectionZ0<masterGridZ0,
    or fillSelectionX1>masterGridX1, or fillSelectionY1>masterGridY1, or fillSelectionZ1>masterGridZ1:
        afviewer.dialogBox("Your fillVolume is outside of your loaded grid. Do you want to",[Recalculate Grid],
                           [Cancel Fill], [Continue]"?"):
            Cancel: return
            Recalculate: masterGrid=None
            Continue: afviewer.dialogBox("Your fill may not place ingredients unless you move the fillVolume to overlap with the masterGrid", [OK])
if masterGrid==None:
    masterBB[0] = fillSelectionObjectBB[0]-pad
    masterBB[1] = fillSelectionObjectBB[1]+pad
    BuildGrid(masterBB,gridSpacing)

if len(Organelles) > 0:
    o_bb = Organelle(orthogonalBoxType=bool, "fillSelectionObject")  #fillSelectionObject can now be a mesh or an orthogonal box
    o_bb.setExteriorRecipe([o_bbExteriorRecipe])
    h1.addOrganelle(o_bb)

if o_bb==None and o_bbExteriorRecipe:
    h1.setExteriorRecipe([ExteriorRecipe])  # No limiting boundingBox, so if there is an exterior recipe, set
                                            #  to infinite... this is the current standard method




#Now, back in HistoVol.py

def BuildGrids(self):
    # FIXME make recursive?
    aInteriorGrids = []
    aSurfaceGrids = []
#    if self.EnviroOnly:
#        v = self.EnviroOnlyCompartiment #the compartiment number
#        if v < 0 and len(self.organelles):
#            organelle = self.organelles[abs(v)-1]
#            aInteriorGrids, aSurfaceGrids = organelle.BuildGridEnviroOnly(self,v)
#        elif  len(self.organelles) :
#            organelle = self.organelles[0]
#            aInteriorGrids, aSurfaceGrids = organelle.BuildGridEnviroOnly(self,1)
#    #aInteriorGrids =[]
#    #aSurfaceGrids =[]
#    else :
    for organelle in self.organelles:
        if organelle.orthogonalBoxType==1:
            a = getPointsInCube(organelle.box, organelleBB[0],organelleBB[1])  #This is the highspeed shortcut for inside points! and no surface! that gets used if the fillSelection is an orthogonal box and there are no other organelles.
        if self.innerGridMethod =="sdf" : # A fillSelection can now be a mesh too... it can use either of these methods
            a, b = organelle.BuildGrid_utsdf(self) # to make the outer most selection from the master and then the organelle
        elif self.innerGridMethod == "bhtree":  # surfaces and interiors will be subtracted from it as normal!
            a, b = organelle.BuildGrid(self)
        aInteriorGrids.append( a)
        aSurfaceGrids.append( b )

    self.grid.aInteriorGrids = aInteriorGrids
    self.grid.aSurfaceGrids = aSurfaceGrids
    print ("build Grids",self.innerGridMethod,len(self.grid.aSurfaceGrids))


