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

"""This module implements shape combination operators
"""

from FlexTree.FTShapes import FTShape

class FTShapesCombiner:

    def __init__(self):
        pass

    def getDescr(self):
        return {}


class FTConcatShapes(FTShapesCombiner):
    """This shape combiner simply appends all shapes into a list"""


    def __init__(self):
        FTShapesCombiner.__init__(self)
        

    def combine(self, shapes):
        """return an FTshape object"""
        node = self.node()
        combinedShape = FTShape(node.molecularFragment, node.name+'Shape')
        for ftshape in shapes:
            assert isinstance(ftshape, FTShape)
            combinedShape.extend(ftshape.geoms)
        return combinedShape


