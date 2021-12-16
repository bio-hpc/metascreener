########################################################################
#
# Date: Jan 2013 Authors: Michel Sanner, Matt Danielson
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI 2013
#
#########################################################################
#
# $Header: /opt/cvs/AutoDockFR/trilinterp.py,v 1.4 2013/11/01 23:09:33 sanner Exp $
#
# $Id: trilinterp.py,v 1.4 2013/11/01 23:09:33 sanner Exp $
#

ENERGYPENALTY = 500.
outsidePenalty = None
from math import floor

def trilinterp(pts, map, inv_spacing, origin):
    """returns a list of values looked up in a 3D grid (map) at
3D locations (tcoords).

INPUT:
    pts           3D coordinates of points to lookup
    map,          grid data (has to be a Numeric array)
    inv_spacing,  1. / grid spacing (3-tuple)
    origin	  minimum coordinates in x, y and z
OUTPUT:
    values        values at points
"""
##
##
## Authors: Garrett M. Morris, TSRI, Accelerated C version 2.2 (C++ code)
##          David Goodsell, UCLA, Original FORTRAN version 1.0 (C code)
##          Michel Sanner (python port)
## Date: 10/06/94, march 26 03

    values = []
    invx, invy, invz = inv_spacing
    xlo, ylo, zlo = origin
    maxx = map.shape[0] - 2
    maxy = map.shape[1] - 2
    maxz = map.shape[2] - 2

    for x,y,z in pts:

        u   = (x-xlo) * invx
        u0  = int(floor(u))
        if u0<0: # outside on X- axis
            #print 'outside on X- axis', x
            return outsidePenalty
            #values.append(outsidePenalty)
            #continue
        elif u0>maxx: # outside on X+ axis
            #print 'outside on X+ axis', x
            return outsidePenalty
            #values.append(outsidePenalty)
            #continue
        else:
            u1 = u0 + 1
            p0u = u - u0
            p1u = 1. - p0u

        v   = (y-ylo) * invy
        v0  = int(floor(v))
        if v0<0: # outside on Y- axis
            #print 'outside on Y- axis', y
            return outsidePenalty
            #values.append(outsidePenalty)
            #continue
        elif v0>maxy: # outside on X+ axis
            #print 'outside on Y+ axis', y
            return outsidePenalty
            #values.append(outsidePenalty)
            #continue
        else:
            v1 = v0 + 1
            p0v = v - v0
            p1v = 1. - p0v

        w   = (z-zlo) * invz
        w0  = int(floor(w))
        if w0<0: # outside on Z- axis
            #print 'outside on Z- axis', z
            return outsidePenalty
            #values.append(outsidePenalty)
            #continue
        elif w0>maxz: # outside on Z+ axis
            #print 'outside on Z+ axis', z
            return outsidePenalty
            #values.append(outsidePenalty)
            #continue
        else:
            w1 = w0 + 1
            p0w = w - w0
            p1w = 1. - p0w

        m = 0.0
        m = m + p1u * p1v * p1w * map[ u0 ][ v0 ][ w0 ]
        m = m + p1u * p1v * p0w * map[ u0 ][ v0 ][ w1 ]
        m = m + p1u * p0v * p1w * map[ u0 ][ v1 ][ w0 ]
        m = m + p1u * p0v * p0w * map[ u0 ][ v1 ][ w1 ]
        m = m + p0u * p1v * p1w * map[ u1 ][ v0 ][ w0 ]
        m = m + p0u * p1v * p0w * map[ u1 ][ v0 ][ w1 ]
        m = m + p0u * p0v * p1w * map[ u1 ][ v1 ][ w0 ]
        m = m + p0u * p0v * p0w * map[ u1 ][ v1 ][ w1 ]

        values.append(m)

    return values
