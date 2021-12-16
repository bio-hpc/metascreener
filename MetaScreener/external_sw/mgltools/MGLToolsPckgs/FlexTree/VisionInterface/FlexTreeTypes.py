## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: April 2006 Authors: Yong Zhao, Guillaume Vareille, Michel Sanner
#
#    sanner@scripps.edu
#    vareille@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Yong Zhao, Guillaume Vareille, Michel Sanner and TSRI
#
# revision:
#
#########################################################################
#
# $Header$
#
# $Id$
#

import numpy.oldnumeric as Numeric

from NetworkEditor.datatypes import AnyType, AnyArrayType


class FlexTreeType(AnyArrayType):

    from FlexTree.FT import FlexTree
    def __init__(self, name='FlexTree', color='#4235FF', shape='rect',
                 width=8, height=8,
                 klass=FlexTree):

        AnyArrayType.__init__(self, name=name, color=color, shape=shape,
                              width=width, height=height,
                              klass=klass)



class FlexTreeNodeType(AnyArrayType):

    from FlexTree.FT import FTNode
    def __init__(self, name='FlexTreeNode', color='#5B91FF', shape='circle',
                 klass=FTNode):

        AnyArrayType.__init__(self, name=name, color=color, shape=shape,
                              klass=klass)



class FlexTreeShapeType(AnyType):
    
    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'FTShape'
        self.data['color'] = '#0F47FF'
        self.data['shape'] = 'pentagon'

    def validate(self, data):
        from FlexTree.FTShapes import FTShape
        return isinstance(data, FTShape)

class FlexTreeMotionType(AnyType):
    
    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'FTMotion'
        self.data['color'] = '#26C9FF'
        self.data['shape'] = 'rect'

    def validate(self, data):
        from FlexTree.FTMotions import FTMotion 
        return isinstance(data, FTMotion)

class FlexTreeConvolutionType(AnyType):
    
    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'FTConvolution'
        self.data['color'] = '#93FFCC'
        self.data['shape'] = 'pentagon'

    def validate(self, data):
        from FlexTree.FTConvolutions import FTShapeMotionConvolve
        return isinstance(data, FTShapeMotionConvolve)

class FlexTreeShapesCombinerType(AnyType):
    
    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'FTCombiner'
        self.data['color'] = '#9B6DFF'
        self.data['shape'] = 'diamond'
        self.data['width'] = 6
        self.data['height'] = 6

    def validate(self, data):
        from FlexTree.FTShapeCombiners import FTShapesCombiner
        return isinstance(data, FTShapesCombiner)

class TransformMatrixType(AnyType):
    """ defines the datatype of 4x4 transformation"""
    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'Transform Matrix'
        self.data['color'] = '#0F47FF'
        self.data['shape'] = 'pentagon'

    def validate(self, data):
        return isinstance(data, Numeric.ArrayType)


class scoreObject(AnyType):
    """ defines the scroing object usable for GA search"""
    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'scoreObject'
        self.data['color'] = '#9B6DFF' #  '#0F47FF'
        self.data['shape'] = 'square'

    def validate(self, data):
        from FlexTree.FTGA import  GAScoring
        return isinstance(data, GAScoring)
