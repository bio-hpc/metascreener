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
@author: Graham Johnson and Michel Sanner with Ludovic Autin
"""


SMALL_NUM = 0.00000001 #anything that avoids division overflow
from math import fabs
import numpy
import AutoFill
helper = AutoFill.helper

## intersect_RayTriangle(): intersect a ray with a 3D triangle
##    Input:  a ray R, and a triangle T
##    Returns -1, None = triangle is degenerate (a segment or point)
##             0, None = disjoint (no intersect)
##             1, I    = intersect in unique point I
##             2, None = are in the same plane

def intersect_RayTrianglePy( ray, Triangle):

    point1 = ray[0]
    point2 = ray[1]
    # get triangle edge vectors and plane normal
    t0 = Triangle[0]
    t1 = Triangle[1]
    t2 = Triangle[2]
    u = [ t1[0]-t0[0], t1[1]-t0[1], t1[2]-t0[2] ]
    
    v = [ t2[0]-t0[0], t2[1]-t0[1], t2[2]-t0[2] ]

    # cross product
    n = ( u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])

    if n[0]*n[0]+n[1]*n[1]+n[2]*n[2]<SMALL_NUM:   # triangle is degenerate
        return -1,None                            # do not deal with this case

    # ray direction vector
    dir = ( point2[0]-point1[0], point2[1]-point1[1], point2[2]-point1[2])

    w0 = ( point1[0]-t0[0], point1[1]-t0[1], point1[2]-t0[2] )
    a = -n[0]*w0[0] - n[1]*w0[1] - n[2]*w0[2]
    b = n[0]*dir[0] + n[1]*dir[1] + n[2]*dir[2]

    if fabs(b) < SMALL_NUM:  # ray is parallel to triangle plane
        if a == 0:           # ray lies in triangle plane
            return 2,None
        else:
            return 0 ,None   # ray disjoint from plane

    # get intersect point of ray with triangle plane
    r = a / b
    if r < 0.0:      # ray goes away from triangle => no intersect
        return 0,None

    #if r > 1.0:      # segment too short => no intersect
    #    return 0,None

    # intersect point of ray and plane
    I = (point1[0] + r*dir[0], point1[1] + r*dir[1], point1[2] + r*dir[2] )

    # is I inside Triangle?
    uu = u[0]*u[0]+u[1]*u[1]+u[2]*u[2]
    uv = u[0]*v[0]+u[1]*v[1]+u[2]*v[2]
    vv = v[0]*v[0]+v[1]*v[1]+v[2]*v[2]
    w = ( I[0] - t0[0], I[1] - t0[1], I[2] - t0[2] )
    wu = w[0]*u[0]+w[1]*u[1]+w[2]*u[2]
    wv = w[0]*v[0]+w[1]*v[1]+w[2]*v[2]
    D = uv * uv - uu * vv

    # get and test parametric coords
    s = (uv * wv - vv * wu) / D
    if s < 0.0 or s > 1.0:        # I is outside Triangle
        return 0,None
    t = (uv * wu - uu * wv) / D
    if t < 0.0 or (s + t) > 1.0:  # I is outside Triangle
        return 0,None

    return 1, I                   # I is in Triangle


try:
    from geomutils.geomalgorithms import intersect_RayTriangle
except ImportError:
    print ("shapefit.intersect_RayTriangle.py: defaulting  to python implementation")
    intersect_RayTriangle = intersect_RayTrianglePy
intersect_RayTriangle = intersect_RayTrianglePy


def intersectRayPolyhedron( pol, pt1, pt2, returnAll=False):
    # compute intersection points between a polyhedron defined by a list
    # of triangles (p0, p1, p2) and a ray starting at pt1 and going through pt2
    inter = []
    interi = []
    ray = [list(pt1), list(pt2)]
    for ti, t in enumerate(pol):
        status, interPt = intersect_RayTriangle(ray, t)
        if status==1:
            inter.append(interPt)
            interi.append(ti)

    if returnAll:
        return interi, inter
    
    if len(inter)>0:  # find closest to pt1
        mini=9999999999.0
        for i, p in enumerate(inter):
            v = ( p[0]-pt1[0], p[1]-pt1[1], p[2]-pt1[2] )
            d = v[0]*v[0]+v[1]*v[1]+v[2]*v[2]
            if d < mini:
                mini = d
                interPt = inter[i]
                tind = interi[i]
        return tind, interPt
    else:
        return None, None


def IndexedPolgonsToTriPoints(geom):
    verts = geom.getVertices()
    tri = geom.getFaces()
    assert tri.shape[1]==3
    triv = []
    for t in tri:
       triv.append( [verts[i].tolist() for i in t] )
    return triv

def vlen(vector):
    a,b,c = (vector[0],vector[1],vector[2])
    return (math.sqrt( a*a + b*b + c*c))
    
def f_ray_intersect_polygon(pRayStartPos, pRayEndPos, pQuadranglePointPositions, pQuadranglePointList, pTruncateToSegment):
    #// This function returns TRUE if a ray intersects a triangle.
    #//It also calculates and returns the UV coordinates of said colision as part of the intersection test,
    vLineSlope = pRayEndPos - pRayStartPos;  #  This line segment defines an infinite line to test for intersection
    vTriPolys = pQuadranglePointList;
    vBackface = false;
    vHitCount = 0;
    
    vTriPoints = pQuadranglePointPositions;
    vEpsilon = 0.00001;
    vBreakj = false;
    vCollidePos = None
    j = 0;

    vQuadrangle = 1;  #  Default says polygon is a quadrangle.
    vLoopLimit = 2;   #  Default k will loop through polygon assuming its a quad.
    if (vTriPolys[j+3] == vTriPolys[j+2]):  #  Test to see if quad is actually just a triangle.
        vQuadrangle = 0;  #  Current polygon is not a quad, its a triangle.
        vLoopLimit = 1;  #//  Set k loop to only cycle one time.
    for k in range(vLoopLimit):# (k = 0; k<vLoopLimit; k++)
        vTriPt0 = vTriPoints[vTriPolys[j+0]];  #//  Always get the first point of a quad/tri
        vTriPt1 = vTriPoints[vTriPolys[j+1+k]]; # // Get point 1 for a tri and a quad's first pass, but skip for a quad's second pass
        vTriPt2 = vTriPoints[vTriPolys[j+2+k]]; #//  Get pontt 2 for a tri and a quad's first pass, but get point 3 only for a quad on its second pass.
    
        vE1 = vTriPt1 - vTriPt0;  #//  Get the first edge as a vector.
        vE2 = vTriPt2 - vTriPt0;  #//  Get the second edge.
        h = numpy.cross(vLineSlope, vE2);
        a = numpy.dot(vE1,h);  #//  Get the projection of h onto vE1.
        if (a > -0.00001) and (a < 0.00001)  :#// If the ray is parallel to the plane then it does not intersect it, i.e, a = 0 +/- given rounding slop.
            continue;
        #//  If the polygon is a quadrangle, test the other triangle that comprises it.
        F = 1.0/a; 
        s = pRayStartPos - vTriPt0;  #//  Get the vector from the origin of the triangle to the ray's origin.
        u = F * ( f_dot_product(s,h) );
        if (u < 0.0 ) or (u > 1.0) : continue;
        #/* Break if its outside of the triangle, but try the other triangle if in a quad.
        #U is described as u = : start of vE1 = 0.0,  to the end of vE1 = 1.0 as a percentage.
        #If the value of the U coordinate is outside the range of values inside the triangle,
        #then the ray has intersected the plane outside the triangle.*/
        q = numpy.cross(s, vE1);
        v = F * numpy.dot(vLineSlope,q);
        if (v <0.0) or (u+v > 1.0) : continue;
        #/*  Breai if outside of the triangles v range.
        #If the value of the V coordinate is outside the range of values inside the triangle,
        #then the ray has intersected the plane outside the triangle.
        #U + V cannot exceed 1.0 or the point is not in the triangle. 
        #If you imagine the triangle as half a square this makes sense.  U=1 V=1 would be  in the 
        #lower left hand corner which would be in the second triangle making up the square.*/
        vCollidePos = vTriPt0 + u*vE1 + v*vE2;  #//  This is the global collision position.
        #//  The ray is hitting a triangle, now test to see if its a triangle hit by the ray.
        vBackface = false;
        if (numpy.dot(vLineSlope, vCollidePos - pRayStartPos) > 0) : #//  This truncates our infinite line to a ray pointing from start THROUGH end positions.
            vHitCount+=1;
            if (pTruncateToSegment ) and (vlen(vLineSlope) < vlen(vCollidePos - pRayStartPos))  :
                break; #// This truncates our ray to a line segment from start to end positions.
    
        if (a<0.00001) :
            vBackface = true;#  Test to see if the triangle hit is a backface.
    return vBackface;

def f_ray_intersect_polyhedron(pRayStartPos, pRayEndPos, pPolyhedron, pTruncateToSegment,point=0):
    #//This function returns TRUE if a ray intersects a triangle.
    #//It also calculates and returns the UV coordinates of said colision as part of the intersection test,
    vLineSlope = (pRayEndPos - pRayStartPos)*2.0;  #//  This line segment defines an infinite line to test for intersection
    #var vPolyhedronPos = GetGlobalPosition(pPolyhedron);
    vTriPolys,vTriPoints,vnormals = helper.DecomposeMesh(pPolyhedron,
                                edit=False,copy=False,tri=True,transform=True)   
    #var vTriPoints = pPolyhedron->GetPoints();
    #var vTriPolys = pPolyhedron->GetPolygons();
    vTriPolys = numpy.array(vTriPolys)
    vTriPoints = numpy.array(vTriPoints)
    vBackface = None
    vHitCount = 0;
    #
    #var i;
    #for (i=0; i< sizeof(vTriPoints); i++)  //  Lets globalize the polyhedron.
    #{
    #vTriPoints[i] = vTriPoints[i] + vPolyhedronPos;
    #}
    #
    vEpsilon = 0.00001;
    vBreakj = False;
    vCollidePos = None
    #var j;
#    helper.resetProgressBar()
#    helper.progressBar(label="checking point %d" % point)
    for j in range(len(vTriPolys)):#(j=0; j<sizeof(vTriPolys); j+=4)  //  Walk through each polygon in a polyhedron
        #{
        #//  Loop through all the polygons in an input polyhedron
        vQuadrangle = 1;  #//  Default says polygon is a quadrangle.triangle 
        vLoopLimit = 2;  #//  Default k will loop through polygon assuming its a quad.triangle
#        if (vTriPolys[j+3] == vTriPolys[j+2])  #//  Test to see if quad is actually just a triangle.
        #{
        vQuadrangle = 0;  #//  Current polygon is not a quad, its a triangle.
        vLoopLimit = 1;  #//  Set k loop to only cycle one time.
        #}
        # 
        #var k;
#        p=(j/float(len(vTriPolys)))*100.0
#        helper.progressBar(progress=int(p),label=str(j))
        for k in range(vLoopLimit):# (k = 0; k<vLoopLimit; k++)
            vTriPt0 = vTriPoints[vTriPolys[j][0]];   #//  Always get the first point of a quad/tri
            vTriPt1 = vTriPoints[vTriPolys[j][1+k]]; # // Get point 1 for a tri and a quad's first pass, but skip for a quad's second pass
            vTriPt2 = vTriPoints[vTriPolys[j][2+k]]; #//  Get point 2 for a tri and a quad's first pass, but get point 3 only for a quad on its second pass.
            #
            vE1 = vTriPt1 - vTriPt0;  #//  Get the first edge as a vector.
            vE2 = vTriPt2 - vTriPt0;  #//  Get the second edge.
            h = numpy.cross(vLineSlope, vE2);#or use hostmath ?
            #
            a = numpy.dot(vE1,h);  #//  Get the projection of h onto vE1.
            if (a > -0.00001 )and( a < 0.00001)  :
                continue;#// If the ray is parallel to the plane then it does not intersect it, i.e, a = 0 +/- given rounding slope.
            #//  If the polygon is a quadrangle, test the other triangle that comprises it.
            #
            F = 1.0/a; 
            s = pRayStartPos - vTriPt0;  #//  Get the vector from the origin of the triangle to the ray's origin.
            u = F * ( numpy.dot(s,h) );
            if (u < 0.0 )or( u > 1.0):
                continue; 
            #/* Break if its outside of the triangle, but try the other triangle if in a quad.
            #U is described as u = : start of vE1 = 0.0,  to the end of vE1 = 1.0 as a percentage.
            #If the value of the U coordinate is outside the range of values inside the triangle,
            #then the ray has intersected the plane outside the triangle.*/
            #
            q = numpy.cross(s, vE1);
            v = F * numpy.dot(vLineSlope,q);
            if (v <0.0 )or( u+v > 1.0) :
                continue;  
            #/*  Break if outside of the triangles v range.
            #If the value of the V coordinate is outside the range of values inside the triangle,
            #then the ray has intersected the plane outside the triangle.
            #U + V cannot exceed 1.0 or the point is not in the triangle. 
            #If you imagine the triangle as half a square this makes sense.  U=1 V=1 would be  in the 
            #lower left hand corner which would be in the second triangle making up the square.*/
            #
            vCollidePos = vTriPt0 + u*vE1 + v*vE2;  #//  This is the global collision position.
            #
            #//  The ray is hitting a triangle, now test to see if its a triangle hit by the ray.
            vBackface = False;
            if (numpy.dot(vLineSlope, vCollidePos - pRayStartPos) > 0) : #//  This truncates our infinite line to a ray pointing from start THROUGH end positions.
            #{
                vHitCount+=1;
                if (pTruncateToSegment ) and (vlen(vLineSlope) < vlen(vCollidePos - pRayStartPos)):
                    break; #// This truncates our ray to a line segment from start to end positions.
                if (a<0.00001) : #//  Test to see if the triangle hit is a backface.
                    #//set master grid to organelle->getname inside
                    vBackface = True;
                    #
                    #//  This stuff is specific to our Point inside goals.
                    vBreakj = True;  #//  To see if a point is inside, I can stop at the first backface hit.
                    break;
                else:
                    vBreakj = True;
    return vHitCount;

def f_get_bounding_corners(vertices):
        mini = numpy.min(vertices, 0)
        maxi = numpy.max(vertices, 0)
        return (mini, maxi)
def f_get_array_of_local_orthogonal_points():
    pass
        
def BuildInteriorGrid(pPolygonObject):
    vTruncateToSegment = 0    
    vStartPos=None
    rayend = helper.getObject("RayEnd")
    vEndPos = helper.ToVec(helper.getTranslation(rayend))

    vPolygonObjectPos = helper.getTranslation(pPolygonObject)#GetGlobalPosition(pPolygonObject);
    faces,vertices,vnormals = helper.DecomposeMesh(pPolygonObject,
                                edit=False,copy=False,tri=True,transform=True)    
    vPointArray = numpy.array(vertices) #PolygonObject->GetPoints();
    vPointArrayLength = len(vPointArray);
#    for i in range(vPointArrayLength) :#(i = 0; i < vPointArrayLength; i++)
#        vPointArray[i] = vPointArray[i] + vPolygonObjectPos;

    vBoundingLocal = f_get_bounding_corners(vPointArray)#, vPointArrayLength);
    vLocalOrthogonalArray = f_get_array_of_local_orthogonal_points(vMasterGridPointPositions, vBoundingLocal, vGridSpacing, vGridX, vGridY, vGridZ, 1, 0);
    vLocalOrthogonalPoints = vLocalOrthogonalArray[0];
    vLocalGridVolume = vLocalOrthogonalArray[1];
    vIndex = 0;
    vArrayOfInnerPoints = numpy.zeros((vLocalGridVolume,3))#new(array, vLocalGridVolume);
    vArrayOfInnerPointsIndices = numpy.zeros(vLocalGridVolume,"int")#new(array, vLocalGridVolume);
    for i in range(vLocalGridVolume) :# (i = 0; i < vLocalGridVolume; i++)
        vStartPos = vMasterGridPointPositions[vLocalOrthogonalPoints[i]];
        vTriPlane = pPolygonObject;
        vTruncateToSegment = 0; #//  Set a boolean for our user input switch.
        vRayCollidePos = f_ray_intersect_polyhedron(vStartPos, vEndPos, vTriPlane, vTruncateToSegment);
        if (vRayCollidePos %  2):
            vArrayOfInnerPoints[vIndex] = vMasterGridPointPositions[vLocalOrthogonalPoints[i]];
            vArrayOfInnerPointsIndices[vIndex] = vLocalOrthogonalPoints[i];
            vIndex+=1;

    #//  For now, we'll visualize the array by creating a pointcloud of the surfaceGrid
    vPolygonGridPointsName = "SurfaceLocalGridPoints" + helper.getName(pPolygonObject)#->GetName();
    ptd = helpe.PointCloudObject(vPolygonGridPointsName, vertices=vLocalOrthogonalArray[2] )
#    f_create_new_object_pointCloud(vPolygonGridPointsName, PolygonObject, vGridHolster, vLocalGridVolume, vLocalOrthogonalArray[2]);
    vPolygonGridPointsName = "SurfaceInteriorGridPoints" + helper.getName(pPolygonObject)#pPolygonObject->GetName();
    vArrayOfInnerPoints = vArrayOfInnerPoints[:vIndex]#f_truncate_array_to_known_size(vArrayOfInnerPoints, vIndex, 1);
    ptd = helpe.PointCloudObject(vPolygonGridPointsName, vertices=vArrayOfInnerPoints)
#    f_create_new_object_pointCloud(vPolygonGridPointsName, PolygonObject, vGridHolster, vIndex, vArrayOfInnerPoints);
    return vArrayOfInnerPointsIndices;



#from intersect_RayTriangle import intersectRayPolyhedron, IndexedPolgonsToTriPoints
