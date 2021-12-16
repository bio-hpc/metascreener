## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#########################################################################
#
# Date: Jan 2004 Authors: Michel Sanner, Daniel Stoffler
#
#    sanner@scripps.edu
#    stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, Daniel Stoffler, and TSRI
#
#########################################################################

"""This module defines shape motion convolution operators
"""
import weakref
import numpy.oldnumeric as Numeric

class FTShapeMotionConvolve:

    def __init__(self, ftnode=None):
        if ftnode is not None:
            self.setNode(ftnode)

    def setNode(self, ftnode):
        from FlexTree.FT import FTNode
        assert isinstance(ftnode, FTNode)
        self.node = weakref.ref(ftnode)

    def getDescr(self):
        """return description of this object as dict"""
        return {}

        

class FTConvolveIdentity(FTShapeMotionConvolve):
    """This operator does nothing to the shape"""

    def __init__(self, ftNode=None):
        FTShapeMotionConvolve.__init__(self, ftNode)


    def convolve(self):
        pass


class FTConvolveApplyMatrix(FTShapeMotionConvolve):
    """This operator sets the geometry's matrix"""

    def __init__(self, ftNode):
        FTShapeMotionConvolve.__init__(self,ftNode)


    def convolve(self):
        mat = self.node().localFrame
        shape = self.node().shape
        if mat is not None and shape:
            redrawGeom=None            
            for g in shape.geoms:
                if g.viewer is None:
                    continue
                g.SetRotation(mat.ravel())
                redrawGeom=g
            if redrawGeom:
                redrawGeom.viewer.Redraw()


class FTConvolveApplyMatrixToCoords(FTShapeMotionConvolve):
    """This operator updates the coords of molecule"""

    def __init__(self, ftNode):
        FTShapeMotionConvolve.__init__(self,ftNode)


    def convolve(self):
        #coords = self.node().getCurrentConformation()
        shape = self.node().shape
        if shape is None:
            return

        coords = shape.getCoords()        
        if len(coords) and shape:
            redrawGeom=None
            #print 'lines..2',  self.node().name, coords[0]
            for g in shape.geoms:
                if g.viewer is None:
                    continue
                g.Set(vertices=coords)

                redrawGeom=g
            if redrawGeom:
                redrawGeom.viewer.Redraw()


class FTConvolveAppendInstanceMatrix(FTShapeMotionConvolve):
    """This operator append the current transformation to the list of
instanceMatrices to the shape"""

    def __init__(self, ftNode):
        FTShapeMotionConvolve.__init__(self,ftNode)


    def convolve(self):
        node = self.node()
        shape = node.shape
        if shape is None:
            return

        #node._updateLocalFrame()  # should I call this here ?
                                  # or can I assume it is up to date ?
        mat = node.localFrame.copy()
        redrawGeom=None
        for g in shape.geoms:
            if g.viewer is None:
                continue
            g.Set(instanceMatrices=g.instanceMatricesFortran+[mat])
            redrawGeom=g

        if redrawGeom:
            redrawGeom.viewer.Redraw()
