# -*- coding: utf-8 -*-
"""
Created 2012

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
# This file is part of autoPACK, cellPACK, and AutoFill.
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

Name: 'randomRot'
@author: Modified from uniform random rotation matrix from http://www.lfd.uci.edu/~gohlke/code/transformations.py.html which is copyrighted as follows:
    
#    # -*- coding: utf-8 -*-
#    # transformations.py
#    
#    # Copyright (c) 2006-2012, Christoph Gohlke
#    # Copyright (c) 2006-2012, The Regents of the University of California
#    # Produced at the Laboratory for Fluorescence Dynamics
#    # All rights reserved.
#    #
#    # Redistribution and use in source and binary forms, with or without
#    # modification, are permitted provided that the following conditions are met:
#    #
#    # * Redistributions of source code must retain the above copyright
#    #   notice, this list of conditions and the following disclaimer.
#    # * Redistributions in binary form must reproduce the above copyright
#    #   notice, this list of conditions and the following disclaimer in the
#    #   documentation and/or other materials provided with the distribution.
#    # * Neither the name of the copyright holders nor the names of any
#    #   contributors may be used to endorse or promote products derived
#    #   from this software without specific prior written permission.
#    #
#    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#    # AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#    # IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#    # ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#    # LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    # CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#    # SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#    # INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#    # CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#    # ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#    # POSSIBILITY OF SUCH DAMAGE.
#    
#    Homogeneous Transformation Matrices and Quaternions.
#
#   A library for calculating 4x4 matrices for translating, rotating, reflecting,
#   scaling, shearing, projecting, orthogonalizing, and superimposing arrays of
#   3D homogeneous coordinates as well as for converting between rotation matrices,
#   Euler angles, and quaternions. Also includes an Arcball control object and
#   functions to decompose transformation matrices.
#
#   :Authors:
#    `Christoph Gohlke <http://www.lfd.uci.edu/~gohlke/>`__,
#    Laboratory for Fluorescence Dynamics, University of California, Irvine
#
#   :Version: 2012.10.18

"""

import numpy
from numpy.random import RandomState
from random import uniform
import math
# epsilon for testing whether a number is close to zero
_EPS = numpy.finfo(float).eps * 4.0


class RandomRot:

    def __init__(self,seed=16):
        self.seedTable= RandomState(seed)
#        from .deg06Rot import allRtotations
#        self.rot = allRtotations
#        self.nbRot = len(allRtotations)-1

    def getOld(self):
        n = int(uniform(0, self.nbRot))
        return self.rot[n]

    def setSeed(self,seed=16):
        self.seedTable= RandomState(seed)

    def get(self):
        return self.random_rotation_matrix()

    def random_quaternion(self,rand=None):
        """Return uniform random unit quaternion.
    
        rand: array like or None
            Three independent random variables that are uniformly distributed
            between 0 and 1.
    
        >>> q = random_quaternion()
        >>> numpy.allclose(1, vector_norm(q))
        True
        >>> q = random_quaternion(numpy.random.random(3))
        >>> len(q.shape), q.shape[0]==4
        (1, True)
    
        """
        if rand is None:
            rand = self.seedTable.rand(3)
#            rand = numpy.random.rand(3)
        else:
            assert len(rand) == 3
        r1 = numpy.sqrt(1.0 - rand[0])
        r2 = numpy.sqrt(rand[0])
        pi2 = math.pi * 2.0
        t1 = pi2 * rand[1]
        t2 = pi2 * rand[2]
        return numpy.array([numpy.cos(t2)*r2, numpy.sin(t1)*r1,
                            numpy.cos(t1)*r1, numpy.sin(t2)*r2])
                            
    def quaternion_matrix(self,quaternion):
        """Return homogeneous rotation matrix from quaternion.
    
        >>> M = quaternion_matrix([0.99810947, 0.06146124, 0, 0])
        >>> numpy.allclose(M, rotation_matrix(0.123, [1, 0, 0]))
        True
        >>> M = quaternion_matrix([1, 0, 0, 0])
        >>> numpy.allclose(M, numpy.identity(4))
        True
        >>> M = quaternion_matrix([0, 1, 0, 0])
        >>> numpy.allclose(M, numpy.diag([1, -1, -1, 1]))
        True
    
        """
        q = numpy.array(quaternion, dtype=numpy.float64, copy=True)
        n = numpy.dot(q, q)
        if n < _EPS:
            return numpy.identity(4)
        q *= math.sqrt(2.0 / n)
        q = numpy.outer(q, q)
        return numpy.array([
            [1.0-q[2, 2]-q[3, 3],     q[1, 2]-q[3, 0],     q[1, 3]+q[2, 0], 0.0],
            [    q[1, 2]+q[3, 0], 1.0-q[1, 1]-q[3, 3],     q[2, 3]-q[1, 0], 0.0],
            [    q[1, 3]-q[2, 0],     q[2, 3]+q[1, 0], 1.0-q[1, 1]-q[2, 2], 0.0],
            [                0.0,                 0.0,                 0.0, 1.0]])

    def random_rotation_matrix(self,rand=None):
        """Return uniform random rotation matrix.
    
        rand: array like
            Three independent random variables that are uniformly distributed
            between 0 and 1 for each returned quaternion.
    
        >>> R = random_rotation_matrix()
        >>> numpy.allclose(numpy.dot(R.T, R), numpy.identity(4))
        True
    
        """
        return self.quaternion_matrix(self.random_quaternion(rand))
## def getRotations(filename):

##     #read rotations
##     f = open(filename)
##     data = f.readlines()
##     f.close()

##     allRot = []
##     for line in data:
##         rotString = line
##         rot = numpy.array( map(float, line.split()))
##         rot.shape = (3,3)
##         allRot.append( rot )

if __name__=='__main__':
    #from time import time
    #t1 = time()
    #allRot = getRotations('deg06.matrix')
    #print 'time to read rotation', time()-t1

##     t1 = time()
##     from deg06Rotations import allRtotations
##     print 'time to import rotation', time()-t1

    
    rr = RandomRot()
    mat = rr.get()
    print(mat)
    
