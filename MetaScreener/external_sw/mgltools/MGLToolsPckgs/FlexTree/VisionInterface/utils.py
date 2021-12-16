#########################################################################
#
# Date: Jan 2004 Author: Daniel Stoffler
#
#    stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler and TSRI
#
#########################################################################

import weakref
import Tkinter

from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.Dial import Dial
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

def addTreeToVision(ed, tree):
    """adds to the Vision FlexTree Library a node that will build a Vision
network of a FlexTree once dragged to the canvas"""
    
    from FlexTree.VisionInterface.FlexTreeNodes import flextreelib
         #FlexTreeLibraryNode
    ed.addLibraryInstance(
        flextreelib, 'FlexTree.VisionInterface.FlexTreeNodes', 'flextreelib')

##     flextreelib.addNode(FlexTreeLibraryNode, tree.name, 'FlexTrees',
##                         kw = { 'flexTree':tree,
##                                'constrkw':{
##                                    'flexTree':'tree'} })
    flextreelib.resizeCategories()


def buildWidget(ftNode):
    """helper method that adds widget to param. panel of Vision node"""
    wdescr = ftNode.motion.widgetsDescr
    visionNode = ftNode.vFTNode()
    row = 0
    column = 0
    for k, v in wdescr.items():
        wframe =Tkinter.Frame(visionNode.paramPanel.widgetFrame)
        lframe =Tkinter.Frame(visionNode.paramPanel.widgetFrame)
        if v['widget'] == 'Dial':
            widget = Dial(wframe, type='float', size=50)
        elif v['widget'] == 'Thumbwheel':
            widget = ThumbWheel(
                wframe, type='float', width=80, height=21,
                wheelPad=2)
        else:
            print 'BUILD TREE ERROR! Illegal widget %s'%v['widget']
            continue
        func = CallBackFunction(
            v['callback'], ftNode.motion, k)
        widget.callbacks.AddCallback(func)
        if v.has_key('min'):
            widget.configure(min=v['min'])
        if v.has_key('max'):
            widget.configure(max=v['max'])
        label = Tkinter.Label(lframe, text=k+':')
        label.pack(fill='both')
        lframe.grid(row=row, column=column, sticky='we')
        wframe.grid(row=row+1, column=column, sticky='we')
        row = row + 1


class RestoreTree:
    """Helper class to restore a FlexTree Vision network. It builds a FlexTree
then assigns the FTNodes to the Vision nodes after the Vision network was
restored."""


    def __init__(self, xml):
        # build FlexTree object
        from FlexTree.XMLParser import ReadXML
        #xml = fixFileName(xml)
        R = ReadXML(xml)
        self.tree = R.get()[0]


    def assignFlexTreeNode(self, visionNode):
        from FlexTree.VisionInterface.FlexTreeNodes import FlexTreeRootNode
        ftNode = self.tree.getNodeByName(visionNode.name)
        visionNode.ftNode = ftNode
        ftNode.vFTNode = weakref.ref(visionNode)
        # and run the nodes in the network
        visionNode.schedule_cb()
        if ftNode.motion is not None:
            buildWidget(ftNode)
        # add to Vision category
        if isinstance(visionNode, FlexTreeRootNode):
            addTreeToVision(visionNode.editor, ftNode.tree())
           

class TreeBuilder:
    """Helper class to build a Vision network from a FlexTree. This class
is inherited from specialized FlexTree Vision nodes"""

    def buildTree(self, flexTree, posx=40, posy=40):
        root = flexTree.root
        # add macro node
        from NetworkEditor.macros import MacroNode

        name = flexTree.name
        if '_' in name:
            name = name.replace('_', '.')
     
        macro = MacroNode(name=name)
        self.editor.currentNetwork.addNode(macro, posx, posy)

        # add flextree nodes, they are added to the upper left corner 
        self._buildTree(macro, root, 37, 78, 37)

        # find largest posy and move macro output node if necessary
        posy = 0
        for node in macro.macroNetwork.nodes:
            posy = max(posy, node.posy)
        opNode = macro.macroNetwork.nodes[1]
        opNode.move(opNode.posx, posy+30, absolute=True)

        # connect root node FlexTree output with macro output node
        rootNode = macro.macroNetwork.nodes[2]
        macro.macroNetwork.connectNodes(rootNode, opNode, 2,0)
        macro.shrink()

        # force macro nod to execute to output all geoms
        macro.run(force=1)

        # unbind motions to have access to motion parameters
        macroNetwork = macro.macroNetwork
        from FlexTree.VisionInterface.FlexTreeNodes import FlexTreeNode
        for node in macro.macroNetwork.nodes:
            if not isinstance(node, FlexTreeNode):
                continue
            if node.ftNode.motion is None:
                continue
            if node.inputPorts[2].widget is not None:
                node.unbindMotion()
                motionNode = macroNetwork.nodes[-1]
                macroNetwork.connectNodes(motionNode, node, 0, 2)

    def _buildTree(self, macro, ftNode, posx, posy, maxX):
        from FlexTree.VisionInterface.FlexTreeNodes import FlexTreeNode, \
             FlexTreeRootNode, flextreelib
        posx = max(posx, maxX)
        gapx = 20  # horizontal constant gap

        if ftNode.parent is None: # root node
            visionNode = FlexTreeRootNode(ftNode=ftNode, name=ftNode.name)
        else:
            visionNode = FlexTreeNode(ftNode=ftNode, name=ftNode.name)

        visionNode.inNodeWidgetsVisibleByDefault = False
        visionNode.library = flextreelib
        # every FlexTree FTNode gets a weakref to the Vision node
        ftNode.vFTNode = weakref.ref(visionNode)
        macro.macroNetwork.addNode(visionNode, posx, posy)
        if ftNode.parent is not None:
            macro.macroNetwork.connectNodes(
                ftNode.parent().vFTNode(), visionNode, 0, 0)
        #macro.macroNetwork.selectNodes([visionNode])

        if ftNode.motion is not None:
            buildWidget(ftNode)

        posy += 90
            
        if len(ftNode.children):
            for child in ftNode.children:
                maxX = max(maxX, self._buildTree(macro, child, posx, posy,
                                                 maxX) )
                posx = posx + visionNode.getSize()[0] + gapx
                maxX = max(posx, maxX)
        else: #leaf node
            # connect geometry port out output node of macro
            opNode = macro.macroNetwork.nodes[1]
            if len(opNode.inputPorts)==1:
                macro.macroNetwork.connectNodes(visionNode, opNode, 1, 0)
            else:
                macro.macroNetwork.connectNodes(visionNode, opNode, 1, 1)
                
        return maxX
