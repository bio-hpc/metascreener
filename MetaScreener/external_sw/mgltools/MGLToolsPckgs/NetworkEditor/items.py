# Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: Nov. 2001  Author: Michel Sanner, Daniel Stoffler
#
#       sanner@scripps.edu
#       stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, Daniel Stoffler and TSRI
#
# revision: Guillaume Vareille
#  
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/NetworkEditor/items.py,v 1.441 2014/03/28 20:53:56 sanner Exp $
#
# $Id: items.py,v 1.441 2014/03/28 20:53:56 sanner Exp $
#

import warnings, re, sys, os, user, inspect, copy, cmath, math, types, weakref
import copy, random
import string, threading, traceback
import Tkinter, Pmw, tkFileDialog, Image, ImageTk
import numpy.oldnumeric as Numeric
import numpy

from tkSimpleDialog import askstring
from mglutil.util.packageFilePath import getResourceFolderWithVersion
from NetworkEditor.ports import InputPort, OutputPort, RunNodeInputPort, \
     TriggerOutputPort, SpecialOutputPort
from mglutil.util.callback import CallBackFunction
from mglutil.util.uniq import uniq
from mglutil.util.misc import ensureFontCase
from mglutil.util.misc import suppressMultipleQuotes
from NetworkEditor.widgets import widgetsTable
from NetworkEditor.Editor import NodeEditor
from NetworkEditor.ports import InputPortsDescr, OutputPortsDescr, Port

# FIXME .. dependency on Vision is bad here
from mglutil.util.packageFilePath import findFilePath
ICONPATH = findFilePath('Icons', 'Vision')

# namespace note: node's compute function get compiled using their origin
# module's __dict__ as global name space

from itemBase import NetworkItems

class NetworkNodeBase(NetworkItems):
    """Base class for a network editor Node
    """
    def __init__(self, name='NoName', sourceCode=None, originalClass=None,
                 constrkw=None, library=None, progbar=0, **kw):

        NetworkItems.__init__(self, name)
        self.objEditor = None # will be an instance of an Editor object
        self.network = None    # VPE network

        self.originalClass = originalClass
        if originalClass is None:
            self.originalClass = self.__class__

        if library is not None:
            assert library.modName is not None, "ERROR: node %s create with library %s that has no modname"%(name, library.name)
            assert library.varName is not None, "ERROR: node %s create with library %s that has no varName"%(name, library.name)

        self.library = library
        
        self.options = kw
        if constrkw is None:
            constrkw = {}
        self.constrkw = constrkw # dictionary of name:values to be added to
                                 # the call of the constructor when node
                                 # is instanciated from a saved network
                                 # used in getNodeSourceCode and
                                 # getNodesCreationSourceCode
        if not sourceCode:
            sourceCode = """def doit(self):\n\tpass\n"""
        self.setFunction(sourceCode)

        self.readOnly = False

        #self.mtstate = 0 # used by MTScheduler to schedule nodes in sub-tree
        #self.thread = None # will hold a ThreadNode object
        
        self.newData = 0            # set to 1 by outputData of parent node
        self.widthFirstTag = 0      # tag used by widthFirstTraversal
        self.isRootNode = 1 # when a node is created it isnot yet a child
        self.forceExecution = 0 # if the forceExecution flag is set
            # we will always run, else we check if new data is available
        self.expandedIcon = False       # True when widgets in node are shown
        self.widgetsHiddenForScale = False # will be set to true if node scales
                                           # below 1.0 while widget are seen

        # does the node have a progrs bar ?
        self.hasProgBar = progbar
        if self.hasProgBar:
            self.progBarH = 3 # Progress bar width
        else:
            self.progBarH = 0
            
        self.scaleSum = 1.0 # scale factor for this node's icon
        
        self.highlightOptions = {'highlightbackground':'red'}
        self.unhighlightOptions = {'highlightbackground':'gray50'}
        self.selectOptions = {'background':'yellow'}
        self.deselectOptions = {'background':'gray85'}

        self.posx = 0         # position where node will be placed on canvas
        self.posy = 0         # these vales are set in the addNode method of
                              # the canvas to which this node is added
                              # the are the upper left corner if self.innerBox
        self.center = [0,0]   # center of innerBox
        
        self.inputPorts = []  # will hold a list of InputPort objects
        self.outputPorts = [] # will hold a list of OutputPort objects

        self._inputPortsID = 0  # used to assign InputPorts a unique number
        self._outputPortsID = 0 # used to assign OutputPorts a unique number

        self._id = None        # a unique node number, which is assigned in
                               # network.addNodes()

        #self.widgets = {}     # {widgetName: PortWidget object }
        #                      # Used to save the widget when it is unbound
        self.specialInputPorts = []
        self.specialOutputPorts = []
        self.specialPortsVisible = False
        self.children = [] # list of children nodes
        self.parents = [] # list of parent nodes
        self.nodesToRunCache = [] # list of nodes to be run when this node
                                  # triggers
        self.condition = None

        self.funcEditorDialog = None

        # ports description, these dictionaries are used to create ports
        # at node's instanciation
        self.inputPortsDescr = InputPortsDescr(self) # [{optionName:optionValue}]
        self.outputPortsDescr = OutputPortsDescr(self) # [{optionName:optionValue}]

        self.widgetDescr = {}  # {widgetName: {optionName:optionValue}}

        self.mouseAction['<Button-1>'] = self.showParams_cb
        self.mouseAction['<Double-Shift-Button-1>'] = self.toggleNodeExpand_cb
        self.mouseAction['<Shift-Button-1>'] = self.startMoveOneNode

        self.hasMoved = False   # set to True in net.moveSubGraph()


    def customizeConnectionCode(self, conn, name, indent=''):
        return []
    
    def showParams_cb(self, event=None):
        ed = self.getEditor()
        ed.libTree.showNodeParameters(self.paramPanel.mainFrame)


    def resize(self, event):
        return
    

    def onStoppingExecution(self):
        pass


    def beforeAddingToNetwork(self, network):
        NetworkItems.beforeAddingToNetwork(self, network)


    def safeName(self, name):
        """remove all weird symbols from node name so that it becomes a
regular string usabel as a Python variable in a saved network
"""
        name = name.replace(' ', '_') # name cannot contain spaces
        if name[0].isdigit():  # first letter cannot be a number
            name = '_'+name
        if name.isalnum(): return name
        if name.isdigit(): return name
        # replace weird characters by '_'
        newname = ''
        for c in name:
            if c.isalnum():
                newname += c
            else:# if c in ['/', '\\', '~', '$', '!']:
                newname+= '_'
        return newname
    
        
    def getUniqueNodeName(self):
        return '%s_%d'%(self.safeName(self.name), self._id)


    def configure(self, **kw):
        """Configure a NetworkNode object. Going through this framework tags
the node modified. Supports the following keywords:
name:       node name (string)
position:   node position on canvas. Must be a tuple of (x,y) coords
function:   the computational method of this node
expanded:   True or False. If True: expand the node
specialPortsVisible: True or False. If True: show the special ports
paramPanelImmediate: True or False. This sets the node's paramPanel immediate
                     state
"""

        ed = self.getEditor()
        
        for k,v in kw.items():
            if k == 'function':
                #solves some \n issues when loading saved networks
                v = v.replace('\'\'\'', '\'')
                v = v.replace('\"\"\"', '\'')
                v = v.replace('\'', '\'\'\'')
                #v = v.replace('\"', '\'\'\'')
                kw[k] = v
                self.setFunction(v, tagModified=True)
            elif ed is not None and ed.hasGUI:
                if k == 'name':
                    self.rename(v, tagModified=True)
                elif k == 'position':
                    self.move(v[0], v[1], absolute=True, tagModified=True)
                elif k == 'expanded':
                    if self.isExpanded() and v is False:
                        self.toggleNodeExpand_cb()
                    elif not self.isExpanded() and v is True:
                        self.toggleNodeExpand_cb()
                elif k == 'specialPortsVisible':
                    if self.specialPortsVisible and v is False:
                        self.hideSpecialPorts(tagModified=True)
                    elif not self.specialPortsVisible and v is True:
                        self.showSpecialPorts(tagModified=True)
                elif k == 'paramPanelImmediate':
                    self.paramPanel.setImmediate(immediate=v, tagModified=True)
                elif k == 'frozen':
                    if self.frozen is True and v is False:
                        self.toggleFrozen_cb()
                    elif self.frozen is False and v is True:
                        self.toggleFrozen_cb()
                    
                
    def getDescr(self):
        """returns a dict with the current configuration of this node"""
        cfg = {}
        cfg['name'] = self.name
        cfg['position'] = (self.posx, self.posy)
        cfg['function'] = self.sourceCode
        cfg['expanded'] = self.isExpanded()
        cfg['specialPortsVisible'] = self.specialPortsVisible
        cfg['paramPanelImmediate'] = self.paramPanel.immediateTk.get()
        cfg['frozen'] = self.frozen
        return cfg


    def rename(self, name, tagModified=True):
        """Rename a node. remember the name has changed, resize the node if
necessary"""
        if name == self.name or name is None or len(name)==0:
            return
        # if name contains ' " remove them
        name = name.replace("'", "")
        name = name.replace('"', "")
        
        self.name=name
        if self.iconMaster is None:
            return
        canvas = self.iconMaster
        canvas.itemconfigure(self.textId, text=self.name)
        self.autoResizeX()
        if tagModified is True:
            self._setModified(True)


    def displayName(self, displayedName, tagModified=True):
        """display the displyed node name. remember the name has changed, resize the node if
necessary"""
        if displayedName is None or len(displayedName)==0:
            return
        # if name contains ' " remove them
        displayedName = displayedName.replace("'", "")
        displayedName = displayedName.replace('"', "")
        
        if self.iconMaster is None:
            return
        canvas = self.iconMaster
        canvas.itemconfigure(self.textId, text=displayedName)
        self.autoResizeX()
        if tagModified is True:
            self._setModified(True)


    def ischild(self, node):
        """returns True is self is a child node of node
"""
        conn = self.getInConnections()
        for c in conn:
            if c.blocking is True:
                node2 = c.port1.node
                if node2 == node:
                    return True                   
                else:
                    return node2.ischild(node)
        return False

        
    def isMacro(self):
        """Returns False if this node is not a MacroNode, returns True if
        MacroNode"""
        
        return False
    
            
    def startMoveOneNode(self, event):
        # get a handle to the network of this node
        net = self.network
        # save the current selection
        if len(net.selectedNodes):
            self.tempo_curSel = net.selectedNodes[:]
            # clear the current selection
            net.clearSelection()
        # select this node so we can move it
        net.selectNodes([self], undo=0)
        # call the function to register functions for moving selected nodes
        net.moveSelectedNodesStart(event)
        # register an additional function to deselect this node
        # and restore the original selection
        num = event.num
        # FIXME looks like I am binding this many times !
        net.canvas.bind("<ButtonRelease-%d>"%num, self.moveSelectedNodeEnd,'+')

    def moveSelectedNodeEnd(self, event):
        # get a handle to the network of this node
        net = self.network
        # clear the selection (made of this node)
        net.clearSelection()
        # if we saved a selection when we started moving this node, restore it
        if hasattr(self, 'tempo_curSel'):
            net.selectNodes(self.tempo_curSel, undo=0)
            del self.tempo_curSel
        net.canvas.unbind("<ButtonRelease-%d>"%event.num)
        self.updateCenter()
        

    def updateCenter(self):
        canvas = self.network.canvas
        if canvas is None: return
        bb = canvas.bbox(self.innerBox)
        cx = self.posx + (bb[2]-bb[0])/2
        cy = self.posy + (bb[3]-bb[1])/2
        self.center = [cx,cy]

        
    def isModified(self):
        # loop over all input ports, all widgets, all outputports, and report
        # if anything has been modified
        modified = False
        if self._modified:
            return True

        # input ports and widgets
        for p in self.inputPorts:
            if p._modified:
                modified = True
                break
            if p.widget:
                if p.widget._modified:
                    modified = True
                    break
        if modified is True:
            return modified

        # output ports
        for p in self.outputPorts:
            if p._modified:
                modified = True
                break

        return modified

        
    def resetModifiedTag(self):
        """set _modified attribute to False in node, ports, widgets."""
        
        self._modified = False
        for p in self.inputPorts:
            p._modified = False
            if p.widget:
                p.widget._modified = False
        for p in self.outputPorts:
            p._modified = False


    def resetTags(self):
        """set _modified attribute to False in node, ports, widgets.
        Also, sets _original attribute to True in node, ports, widgets
        And we also reset the two flags in all connections from and to ports"""
        
        self._modified = False
        self._original = True
        for p in self.inputPorts:
            p._modified = False
            p._original = True
            if p.widget:
                p.widget._modified = False
                p.widget._original = True
            for c in p.connections:
                c._modified = False
                c._original = True
                
        for p in self.outputPorts:
            p._modified = False
            p._original = True
            for c in p.connections:
                c._modified = False
                c._original = True
                

    def getInputPortByName(self, name):
        # return the an input port given its name
        for p in self.inputPorts:
            if p.name==name:
                return p
        warnings.warn(
            'WARNING: input port "%s" not found in node %s'%(name, self.name))


    def getOutputPortByName(self, name):
        # return the an output port given its name
        for p in self.outputPorts:
            if p.name==name:
                return p
        warnings.warn(
            'WARNING: output port "%s" not found in node %s'%(name, self.name))

    def getOutputPortByType(self, type, name=None):
        # return the matching or first output port given its type
        if len(self.outputPorts) == 0:
            return None
        
        lDatatypeObject = \
              self.outputPorts[0].getDatatypeObjectFromDatatype(type)
                                                                
        lPort = None
        for p in self.outputPorts:            
            if p.datatypeObject == lDatatypeObject:
                if p.name == name:
                    return p
                elif p is None:
                    return p                  
                elif lPort is None:
                    lPort = p
        if lPort is not None:   
            return lPort                
        
        return None
        
    def getSpecialInputPortByName(self, name):
        # return the an input port given its name
        for p in self.specialInputPorts:
            if p.name==name:
                return p
        warnings.warn(
            'WARNING: special input port "%s" not found in node %s'%(name, self.name))


    def getSpecialOutputPortByName(self, name):
        # return the an output port given its name
        for p in self.specialOutputPorts:
            if p.name==name:
                return p
        warnings.warn(
            'WARNING: special output port "%s" not found in node %s'%(name, self.name))


    def getInConnections(self):
        l = []
        for p in self.inputPorts:
            l.extend(p.connections)
        for p in self.specialInputPorts:
            l.extend(p.connections)
        return l


    def getOutConnections(self):
        l = []
        for p in self.outputPorts:
            l.extend(p.connections)
        for p in self.specialOutputPorts:
            l.extend(p.connections)
        return l


    def getConnections(self):
        return self.getInConnections()+self.getOutConnections()


    def getWidgetByName(self, name):
        port = self.inputPortByName[name]
        if port:
            if port.widget:
                return port.widget
        

##############################################################################
# The following methods are needed to save a network
# getNodeDefinitionSourceCode() is called by net.getNodesCreationSourceCode()
##############################################################################
        
    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):
        """This method builds the text-string to describe a network node
in a saved file.
networkName: string holding the networkName
indent: string of whitespaces for code indentation. Default: ''
ignoreOriginal: True/False. Default: False. If set to True, the node's attr
                _original is ignored (used in cut/copy/paste nodes inside a
                macro that came from a node library where nodes are marked
                original
This method is called by net.getNodesCreationSourceCode()
NOTE: macros.py MacroNode re-implements this method!"""

        lines = []
        nodeName = self.getUniqueNodeName()
        self.nameInSavedFile = nodeName

        ##################################################################
        # add lines to import node from library, instanciate node, and
        # add node to network
        ##################################################################
        indent, l = self.getNodeSourceCodeForInstanciation(
            networkName, indent=indent, ignoreOriginal=ignoreOriginal)
        lines.extend(l)

        ##################################################################
        # fetch code that desccribes the changes done to this node compared
        # to the base class node
        ##################################################################
        txt = self.getNodeSourceCodeForModifications(
            networkName, indent=indent, ignoreOriginal=ignoreOriginal)
        lines.extend(txt)

        txt = self.getStateDefinitionCode(nodeName=nodeName,indent=indent)
        lines.extend(txt)

        return lines


    def getStateDefinitionCode(self, nodeName, indent=''):
        #print "getStateDefinitionCode"
        return ''


    def getNodeSourceCodeForModifications(self, networkName, indent="",
                                          ignoreOriginal=False):
        """Return the code that describes node modifications compared to the
original node (as described in a node library)"""

        lines = []
        
        ##################################################################
        # add lines for ports if they changed compared to the base class
        ##################################################################
        indent, l =  self.getNodeSourceCodeForPorts(networkName, indent , ignoreOriginal)
        lines.extend(l)

        ##################################################################
        # add lines for widgets: add/delete/configure/unbind, and set value
        ##################################################################
        indent, l =  self.getNodeSourceCodeForWidgets(networkName, indent,
                                                      ignoreOriginal)
        lines.extend(l)

        ##################################################################
        # add lines for node changes (name, expanded, etc)
        ##################################################################
        indent, l = self.getNodeSourceCodeForNode(networkName, indent,
                                                  ignoreOriginal)
        lines.extend(l)

        return lines


    def getNodeSourceCodeForInstanciation(self, networkName="masterNet",
                                          indent="", ignoreOriginal=False,
                                          full=0):
        """This method is called when saving a network. Here, code is
generated to import a node from a library, instanciate the node, and adding it
to the network."""
        
        lines = []
        ed = self.getEditor()
        nodeName = self.getUniqueNodeName()

        ##################################################################
        # Abort if this node is original (for example, inside a macro node)
        ##################################################################
        if self._original is True and not full and not ignoreOriginal:
            return indent, lines

        ed._tmpListOfSavedNodes[nodeName] = self
        
        k = self.__class__

        ##################################################################
        # add line to import node from the library
        ##################################################################
        if self.library is not None:
            libName = self.library.varName
            lines.append(indent + "klass = %s.nodeClassFromName['%s']\n"%(libName, k.__name__))
        else:
            pathStr = str(k)[8:-2] # i.e. 'NetworkEditor.Tests.nodes.PassNode'
            klass = pathStr.split('.')[-1] # i.e. PassNode
            path = pathStr[:-len(klass)-1] # i.e. NetworkEditor.Tests.nodes
            libName = None
            lines.append(indent + "from %s import %s\n"%(path, klass))
            lines.append(indent + "klass = %s\n"%klass)
            #if self.library.file is not None: # user defined library
##             if False: # skip this test!!
##                 l = "from mglutil.util.packageFilePath import "+\
##                     "getObjectFromFile\n"
##                 lines.append(indent+l)
##                 lines.append(indent+"%s = getObjectFromFile( '%s', '%s')\n"%(
##                     k.__name__, self.library.file, k.__name__))
##             else:
##             line = "from "+k.__module__+" import "+k.__name__+"\n"
##             lines.append(indent+line)
##         else:

        # generate from EwSignal import EwSignalCollector
        #line = "from "+k.__module__+" import "+k.__name__+"\n"
        #lines.append(indent+line)

        # generate klass = EwSignal.nodeClassFromName['EwSignalCollector']
        #line = "klass = %s.nodeClassFromName['%s']\n"%(self.library.varName,
        #                                               k.__name__)
        #lines.append(indent+line)
       
        ##################################################################
        # add line with constructor keywords if needed
        ##################################################################
        constrkw = ''
        for name, value in self.constrkw.items():
            constrkw = constrkw + name+'='+str(value)+', '

        # this line seems redondant, 
        # but is usefull when the network is saved and resaved
        # especially with pmv nodes
        constrkw = constrkw + "constrkw="+str(self.constrkw)+', '

        ##################################################################
        # add line to instanciate the node
        ##################################################################
        #line=nodeName+" = "+k.__name__+"("+constrkw+"name='"+\
        #      self.name+"'"
        line=nodeName+" = klass("+constrkw+"name='"+\
              self.name+"'"
        if libName is not None:
            line = line + ", library="+libName
        line = line + ")\n"
        lines.append(indent+line)

        ##################################################################
        # add line to add the node to the network
        ##################################################################
        txt = networkName+".addNode("+nodeName+","+str(self.posx)+","+\
              str(self.posy)+")\n"
        lines.append(indent+txt)
        return indent, lines
    

    def getNodeSourceCodeForPorts(self, networkName, indent="",
                                  ignoreOriginal=False,full=0,
                                  dummyNode=None, nodeName=None):
        """Create code used to save a network which reflects changes of ports
compared to the port definitions in a given network node of a node library.
We create text to configure a port with changes, adding a port or deleting
a port. If optional keyword 'full' is set to 1, we will append text to
configure unchanged ports"""

        lines = []
        ed = self.getEditor()

        if dummyNode is None:
            # we need the base class node
            if issubclass(self.__class__, FunctionNode):
                lKw = {'masternet':self.network}
                lKw.update(self.constrkw)
                dummyNode = apply(self.__class__,(), lKw)
            else:
                dummyNode = self.__class__()
        
        if nodeName is None:
            nodeName = self.getUniqueNodeName()

        ###############################################################
        # created save strings for inputPorts
        ###############################################################
        i = 0
        lDeleted = 0
        for index in range(len(dummyNode.inputPortsDescr)):
            
            # Delete remaining input ports if necessary
            if i >= len(self.inputPorts):
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "%s.deletePort(%s.inputPortByName['%s'])\n"%(
                #txt = "%s.deletePort(%s.getInputPortByName('%s'))\n"%(
                    nodeName, nodeName,
                    dummyNode.inputPortsDescr[index]['name'])
                lines.append(indent+txt)
                continue

            ip = self.inputPorts[i]

            # delete input port
            if ip._id != index:
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "%s.deletePort(%s.inputPortByName['%s'])\n"%(
                #txt = "%s.deletePort(%s.getInputPortByName('%s'))\n"%(
                    nodeName, nodeName,
                    dummyNode.inputPortsDescr[index]['name'])
                lines.append(indent+txt)
                lDeleted += 1
                continue

            # modify input port
            else:
                if ip._modified is True or ignoreOriginal is True:
                    if full:
                        changes = ip.getDescr()
                    else:
                        changes = ip.compareToOrigPortDescr()
                    if len(changes):
                        if nodeName != 'self': 
                            lines = self.checkIfNodeForSavingIsDefined(
                                               lines, networkName, indent)
                        txt = "apply(%s.inputPortByName['%s'].configure, (), %s)\n"%(
                            nodeName, dummyNode.inputPortsDescr[ip._id]['name'], str(changes) )
                        #txt = "apply(%s.inputPorts[%s].configure, (), %s)\n"%(
                        #    nodeName, ip.number, str(changes) )
                        lines.append(indent+txt)
                i = i + 1
                continue

        # check if we have to add additional input ports
        for p in self.inputPorts[len(dummyNode.inputPortsDescr) - lDeleted:]:
            if p._modified is True or ignoreOriginal is True:
                descr = p.getDescr()
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "apply(%s.addInputPort, (), %s)\n"%(
                    nodeName, str(descr) )
                lines.append(indent+txt) 
            

        ###############################################################
        # created save strings for outputPorts
        ###############################################################
        i = 0
        for index in range(len(dummyNode.outputPortsDescr)):

            # Delete remaining output ports if necessary
            if i >= len(self.outputPorts):
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "%s.deletePort(%s.outputPortByName['%s'])\n"%(
                    nodeName, nodeName,
                    dummyNode.outputPortsDescr[index]['name'])
                lines.append(indent+txt)
                continue
                
            op = self.outputPorts[i]

            # delete output port
            if not op._id == index:
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "%s.deletePort(%s.outputPortByName['%s'])\n"%(
                    nodeName, nodeName,
                    dummyNode.outputPortsDescr[index]['name'])
                lines.append(indent+txt)
                continue
                    
            # modify output port
            else:
                if op._modified is True or ignoreOriginal is True:
                    if full:
                        changes = op.getDescr()
                    else:
                        changes = op.compareToOrigPortDescr()
                    if len(changes):
                        if nodeName != 'self': 
                            lines = self.checkIfNodeForSavingIsDefined(
                                               lines, networkName, indent)
                        txt = "apply(%s.outputPortByName['%s'].configure, (), %s)\n"%(
                            nodeName, dummyNode.outputPortsDescr[op._id]['name'], str(changes) )
                        #txt = "apply(%s.outputPorts[%s].configure, (), %s)\n"%(
                        #    nodeName, op.number, str(changes) )
                        lines.append(indent+txt)
                i = i + 1
                continue

        # check if we have to add additional output ports
        for p in self.outputPorts[len(dummyNode.outputPortsDescr):]:
            if p._modified is True or ignoreOriginal is True:
                descr = p.getDescr()
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "apply(%s.addOutputPort, (), %s)\n"%(
                    nodeName, str(descr) )
                lines.append(indent+txt) 

        # makes the specials ports visible if necessary
        if self.specialPortsVisible:           
            if nodeName != 'self': 
                lines = self.checkIfNodeForSavingIsDefined(
                                   lines, networkName, indent)
            txt = "apply(%s.configure, (), {'specialPortsVisible': True})\n"%(nodeName)
            lines.append(indent+txt) 

        return indent, lines


    def getNodeSourceCodeForWidgets(self, networkName, indent="",
                                    ignoreOriginal=False, full=0,
                                    dummyNode=None, nodeName=None):
        """Create code used to save a network which reflects changes of
widgets compared to the widget definitions in a given network node of a
node library.
We create text to configure a widget with changes, adding a widget or deleting
a widget. If optional keyword 'full' is set to 1, we will append text to
configure unchanged widgets."""

        lines = []
        ed = self.getEditor()

        if dummyNode is None:
            # we need the base class node
            if issubclass(self.__class__, FunctionNode):
                lKw = {'masternet':self.network}
                lKw.update(self.constrkw)
                dummyNode = apply(self.__class__,(), lKw)
            else:
                dummyNode = self.__class__()

        if nodeName is None:
            nodeName = self.getUniqueNodeName()

        for i in range(len(self.inputPorts)):
            p = self.inputPorts[i]
            if p._id >= len(dummyNode.inputPortsDescr):
                origDescr = None
            elif p.name != dummyNode.inputPortsDescr[p._id]['name']:
                origDescr = None
            else:
                try:
                    origDescr = dummyNode.widgetDescr[p.name]
                except:
                    origDescr = None
            w = p.widget
            try:
                ownDescr = w.getDescr()
            except:
                ownDescr = None

            #############################################################
            # if current port has no widget and orig port had no widget:
            # continue
            #############################################################
            if ownDescr is None and origDescr is None:
                pass

            #############################################################
            # if current port has no widget and orig port had a widget:
            # unbind the widget. Also, check if the port was modified:
            # unbinding and deleting a widget sets the port._modifed=True
            #############################################################
            elif ownDescr is None and origDescr is not None:
                if (p._modified is True) or (ignoreOriginal is True):
                    if nodeName != 'self': 
                        lines = self.checkIfNodeForSavingIsDefined(
                                           lines, networkName, indent)
                    ## distinguish between "delete" and "unbind":
                    # 1) Delete event (we don't have _previousWidgetDescr)
                    if p._previousWidgetDescr is None:
                        txt = "%s.inputPortByName['%s'].deleteWidget()\n"%(
                            nodeName, self.inputPortsDescr[i]['name'])
                        #txt = "%s.inputPorts[%d].deleteWidget()\n"%(
                        #    nodeName, i)
                        lines.append(indent+txt)
                    # 2) unbind event (we have _previousWidgetDescr)
                    else:
    
    
                        # first, set widget to current value
                        txt1 =  self.getNodeSourceCodeForWidgetValue(
                            networkName, i, indent, ignoreOriginal, full)
                        lines.extend(txt1)
                        # then unbind widget
                        
                        txt2 = "%s.inputPortByName['%s'].unbindWidget()\n"%(
                            nodeName, self.inputPortsDescr[i]['name'])
                        #txt2 = "%s.inputPorts[%d].unbindWidget()\n"%(
                        #    nodeName, i)
                        lines.append(indent+txt2)

            #############################################################
            # if current port has widget and orig port had no widget:
            # create the widget
            #############################################################
            elif ownDescr is not None and origDescr is None:
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                # create widget
                txt = \
                 "apply(%s.inputPortByName['%s'].createWidget, (), {'descr':%s})\n"%(
                    nodeName, self.inputPortsDescr[i]['name'], str(ownDescr ) )
                #txt = \
                # "apply(%s.inputPorts[%d].createWidget, (), {'descr':%s})\n"%(
                #     nodeName, i, str(ownDescr ) )
                lines.append(indent+txt)

                # Hack to set widget. This fixes the ill sized nodes
                # when new widgets have been added to a node (MS)
                wmaster = ownDescr.get('master', None)
                if wmaster=='node':
                    txt = "%s.inputPortByName['%s'].widget.configure(master='node')\n"%(nodeName, self.inputPortsDescr[i]['name'])
                lines.append(indent+txt)

                # set widget value
                txt = self.getNodeSourceCodeForWidgetValue(
                    networkName, i, indent, ignoreOriginal, full, nodeName)
                lines.extend(txt)
                
            #############################################################
            # if current port has widget and orig port has widget:
            # check if both widgets are the same, then check if changes
            # occured.
            # If widgets are not the same, delete old widget, create new
            #############################################################
            elif ownDescr is not None and origDescr is not None:
                if ownDescr['class'] == origDescr['class']:
                    if p.widget._modified is True or ignoreOriginal is True:
                        if full:
                            changes = ownDescr
                        else:
                            changes = w.compareToOrigWidgetDescr()
                        if len(changes):
                            if nodeName != 'self': 
                                lines = self.checkIfNodeForSavingIsDefined(
                                                   lines, networkName, indent)

                            if changes.has_key('command'):
                                # extract and build the correct CB function name
                                lCommand = changes['command']
                                lCommandStr = str(lCommand)
                                lCbIndex = lCommandStr.find('.')
                                lCbFuncName = nodeName + lCommandStr[lCbIndex:]
                                lCbIndex = lCbFuncName.find(' ')
                                lCbFuncName = lCbFuncName[:lCbIndex]
                                changes['command'] = lCbFuncName
                                
                                # the changes['command'] is now a string
                                # so, we need to get rid of the quote 
                                # that comes with the output
                                lChangesStr = str(changes)  
                                lQuoteIndex = lChangesStr.find(lCbFuncName) 
                                lChanges = lChangesStr[:lQuoteIndex-1] + \
                                       lCbFuncName + \
                                       lChangesStr[lQuoteIndex+len(lCbFuncName)+1:]  
                            else:
                                lChanges = str(changes)
                                
                            txt = \
                            "apply(%s.inputPortByName['%s'].widget.configure, (), %s)\n"%(
                                nodeName, self.inputPortsDescr[i]['name'], lChanges)
                            #txt = \
                            #"apply(%s.inputPorts[%d].widget.configure, (), %s)\n"%(
                            #    nodeName, i, str(changes))
                            lines.append(indent+txt)
                else:
                    if nodeName != 'self': 
                        lines = self.checkIfNodeForSavingIsDefined(
                                           lines, networkName, indent)
                    txt1 = "%s.inputPortByName['%s'].deleteWidget()\n"%(
                        nodeName, self.inputPortsDescr[i]['name'])
                    #txt1 = "%s.inputPorts[%d].deleteWidget()\n"%(
                    #    nodeName,i)
                    txt2 = \
                     "apply(%s.inputPortByName['%s'].createWidget, (), {'descr':%s})\n"%(
                               nodeName, self.inputPortsDescr[i]['name'], str(ownDescr) )
                    #txt2 = \
                    #"apply(%s.inputPorts[%d].createWidget, (), {'descr':%s})\n"%(
                    #           nodeName, i, str(ownDescr) )
                    lines.append(indent+txt1)
                    lines.append(indent+txt2)
                # and set widget value
                txt = self.getNodeSourceCodeForWidgetValue(
                    networkName, i, indent, ignoreOriginal, full, nodeName)
                lines.extend(txt)
                    
        return indent, lines


    def getNodeSourceCodeForWidgetValue(self, networkName, portIndex,
                                        indent="", ignoreOriginal=False,
                                        full=0, nodeName=None):
        """Returns code to set the widget value. Note: here we have to take
        unbound widgets into account."""
        
        #############################################################
        # Setting widget value sets widget _modified=True
        #############################################################
        lines = []
        returnPattern = re.compile('\n') # used when data is type(string)

        p = self.inputPorts[portIndex]

        # we need the base class node
        if issubclass(self.__class__, FunctionNode):
            lKw = {'masternet':self.network}
            lKw.update(self.constrkw)
            dummyNode = apply(self.__class__,(), lKw)
        else:
            dummyNode = self.__class__()
        
        if nodeName is None:
            nodeName = self.getUniqueNodeName()

        #############################################################
        # Get data and original widget description to check if value
        # changed
        #############################################################
        ## do we have a widget ?
        if p.widget:
            ## is it an original widget?
            try:
                origDescr = dummyNode.widgetDescr[p.name]
            except:
                ## or a new widget
                origDescr = {}
            val = p.widget.getDataForSaving()

        ## do we have an unbound widget ?
        elif p.widget is None and p._previousWidgetDescr is not None:
            origDescr = p._previousWidgetDescr
            val = p._previousWidgetDescr['initialValue']
        ## no widget ?
        else:
            return lines

        #############################################################
        # Compare data to default value, return if values are the same
        #############################################################

##         ## CASE 1: BOUND WIDGET:
##         if p.widget:
##             # MS WHY ignor original when cut and copy???
##             # ignoreOriginal is set True when cut|copy
##             #if not p.widget._modified and not ignoreOriginal:
##             #    return lines

##             # 1) compare value to initial value of widget descr
##             wdescr = p.widget.getDescr()
##             if wdescr.has_key('initialValue'):
##                 if val==wdescr['initialValue']: # value is initial value
##                     return lines

##             # 2) else: compare to initialValue in node base class definition
##             else:
##                 # 3) if the widget's original description has an initialValue
##                 if origDescr.has_key('initialValue'):
##                     if val == origDescr['initialValue']:
##                         return lines
##                 # 4) else, compare to widget base class defined initialValue
##                 else:
##                     origWidgetDescr = p.widget.__class__.configOpts
##                     if val == origWidgetDescr['initialValue']['defaultValue']:
##                         return lines
 
##         ## CASE 2: UNBOUND WIDGET:
##         else:
##             descr = dummyNode.widgetDescr[p.name]
##             #if descr.has_key('initialValue') and val == descr['initialValue']:
##             #    return lines

        #############################################################
        # Create text to save widget value
        #############################################################
        if nodeName != 'self': 
            lines = self.checkIfNodeForSavingIsDefined(
                               lines, networkName, indent)
        if p.widget is None:
            #widget has been unbinded in the before or after adding to network
            #as it will be unbinded later we can safely rebind it to set the widget
            datatxt = '%s.inputPortByName[\'%s\'].rebindWidget()\n'%( 
                       nodeName, self.inputPortsDescr[portIndex]['name'])
            lines.append(indent+datatxt)

        if type(val)==types.StringType:
            if returnPattern.search(val): #multi - line data
                datatxt = \
                    '%s.inputPortByName[\'%s\'].widget.set(r"""%s""", run=False)\n'%( 
                    nodeName, self.inputPortsDescr[portIndex]['name'], val)
            else:
                datatxt = '%s.inputPortByName[\'%s\'].widget.set(r"%s", run=False)\n'%( 
                    nodeName, self.inputPortsDescr[portIndex]['name'], val)
        else:
            if hasattr(val, 'getDescr'):
                datatxt = '%s.inputPortByName[\'%s\'].widget.set(%s, run=False)\n'%( 
                    nodeName, self.inputPortsDescr[portIndex]['name'], val.getDescr() )
            else:
                datatxt = '%s.inputPortByName[\'%s\'].widget.set(%s, run=False)\n'%( 
                    nodeName, self.inputPortsDescr[portIndex]['name'], val)
        lines.append(indent+datatxt)

        return lines


    def getNodeSourceCodeForNode(self, networkName, indent="", 
                                 ignoreOriginal=False, full=0, nodeName=None):
        """return code to configure a node with modifications compared to
the node definition in a node library. Note: 
"""
        lines = []
        
        if (self._modified is False) and (ignoreOriginal is False):
            return indent, lines
         
        if full:
            changes = self.getDescr().copy()
        else:
            changes = self.compareToOrigNodeDescr()

        if changes.has_key('name'):
            changes.pop('name') # name is passed to constructor
        if changes.has_key('position'):
            changes.pop('position') # position is set in addNode

        if nodeName is None:
            nodeName = self.getUniqueNodeName()

        if changes.has_key('function'):
            changes.pop('function') 
            # function has to be set separately:
            code, i = self.getNodeSourceCodeForDoit(
                networkName=networkName,
                nodeName=nodeName,
                indent=indent,
                ignoreOriginal=ignoreOriginal)
            if code:
                # Note: the line to add the code to the node is returned
                # within 'code'
                lines.extend(code)

        if len(changes):
            txt = "apply(%s.configure, (), %s)\n"%(
                nodeName, str(changes))
            lines.append(indent+txt)

        return indent, lines


    def getNodeSourceCodeForDoit(self, networkName, nodeName,indent="",
                                 ignoreOriginal=False, full=0):
        lines = []
        ed = self.getEditor()
        
        if (self._modified is True) or (ignoreOriginal is True):
            if nodeName != 'self': 
                lines = self.checkIfNodeForSavingIsDefined(
                                   lines, networkName, indent)
            lines.append(indent+"code = \"\"\"%s\"\"\"\n"%self.sourceCode)
            lines.append(indent+"%s.configure(function=code)\n"% nodeName)

        return lines, indent


    def getAfterConnectionsSourceCode(self, networkName, indent="",
                                      ignoreOriginal=False):
        """Here, we provide a hook for users to generate source code which
might be needed to adress certain events after connections were formed:
for example, connections might generate new ports."""
        
        # The MacroOutputNode subclasses this method and returns real data
        lines = []
        return lines


    def compareToOrigNodeDescr(self):
        """compare this node to the original node as defined in a given node
library, such as StandardNodes. Return a dictionary containing the
differences."""
        
        ownDescr = self.getDescr().copy()
        dummy = self.__class__()  # we need to create a base class node
                                  # we dont need to add the self generated port
                                  # as we only look here for the node modifications

        for k,v in ownDescr.items():
            if k == 'name':
                if v == dummy.name:
                    ownDescr.pop(k)

            elif k == 'position':  # this is a bit tricky: the dummy node
            # has not been added to a net yet, thus we assume a new position
                continue

            elif k == 'function':
                #we don't compare the prototype as it is automatically generated
                #the code itself is what may have be changed
                if v[v.find(':'):] == dummy.sourceCode[dummy.sourceCode.find(':'):]:
                    ownDescr.pop(k)

            elif k == 'expanded':
                if v == dummy.inNodeWidgetsVisibleByDefault:
                    ownDescr.pop(k)

            elif k == 'specialPortsVisible':
                if v == dummy.specialPortsVisible:
                    ownDescr.pop(k)

            elif k == 'paramPanelImmediate': # default value is 0
                if v == 0 or v is False:
                    ownDescr.pop(k)

            elif k == 'frozen': # default is False
                if v == dummy.frozen:
                    ownDescr.pop(k)

        return ownDescr
                                 

    def checkIfNodeForSavingIsDefined(self, lines, networkName, indent):
        """This method fixes a problem with saving macros that come from a
node library. If only a widget value has changed, we do not have a handle
to the node. Thus, we need to create this additional line to get a handle
"""
        
        ed = self.getEditor()
        nodeName = self.getUniqueNodeName()

        if ed._tmpListOfSavedNodes.has_key(nodeName) is False:

            # This part is a bit complicated: we need to define the various
            # macro nodes if we have nested macros and they are not explicitly
            # created (e.g. a macro from a node library)
            from macros import MacroNetwork
            if isinstance(self.network, MacroNetwork):
                roots = self.network.macroNode.getRootMacro()
                for macro in roots[1:]: # skip root, because this is always defined!?
                    nn = macro.getUniqueNodeName() # was nn = 'node%d'%macro._id
                    if ed._tmpListOfSavedNodes.has_key(nn) is False:
                        txt = "%s = %s.macroNetwork.nodes[%d]\n"%(
                            nn, macro.network.macroNode.getUniqueNodeName(),
                            macro.network.nodeIdToNumber(macro._id))
                        lines.append(indent+txt)
                        ed._tmpListOfSavedNodes[nn] = macro                        
                        
            # now process the 'regular' nodes
            #import pdb;pdb.set_trace()
            txt = "%s = %s.nodes[%d]\n"%(nodeName, networkName,
                self.network.nodeIdToNumber(self._id))
            lines.append(indent+txt)
            ed._tmpListOfSavedNodes[nodeName] = self
        return lines
    

#############################################################################
#### The following methods are needed to generate source code (not for saving
#### networks)
#############################################################################


    def saveSource_cb(self, dependencies=False):
        """ the classname is extracted from the given filename
"""
        lPossibleFileName = "New" + self.name + ".py"
        lPossibleFileNameSplit = lPossibleFileName.split(' ')
        initialfile = ''
        for lSmallString in lPossibleFileNameSplit:
            initialfile += lSmallString

        userResourceFolder = self.getEditor().resourceFolderWithVersion
        if userResourceFolder is None:
            return
        userVisionDir = userResourceFolder + os.sep + 'Vision' + os.sep
        userLibsDir = userVisionDir + 'UserLibs' + os.sep
        defaultLibDir = userLibsDir + 'MyDefaultLib'

        file = tkFileDialog.asksaveasfilename(
                    initialdir = defaultLibDir , 
                    filetypes=[('python source', '*.py'), ('all', '*')],
                    title='Save source code in a category folder',
                    initialfile=initialfile
                    )

        if file:
            # get rid of the extension and of the path
            lFileSplit = file.split('/')
            name = lFileSplit[-1].split('.')[0]
            self.saveSource(file, name, dependencies)
            # reload the modified library
            self.getEditor().loadLibModule(str(lFileSplit[-3]))


    def saveSource(self, filename, classname, dependencies=False):
        f = open(filename, "w")
        map( lambda x, f=f: f.write(x), 
             self.getNodeSourceCode(classname, 
                                    networkName='self.masterNetwork',
                                    dependencies=dependencies) )
        f.close()


    def getNodeSourceCode(self, className, networkName='self.network',
                          indent="", dependencies=False):
        """This method is called through the 'save source code' mechanism.

Generate source code describing a node. This code can be put 
into a node library. This is not for saving networks.

dependencies: True/False
    False: the node is fully independent from his original node. 
    True : the node is saved as a subclass of the original node, and only 
           modifications from the original are saved. 
"""
        lines = []

        kw = {} # keywords dict
        kw['dependencies'] = dependencies

        indent0 = indent

        txt, indent  = apply(self.getHeaderBlock, (className, indent), kw)
        lines.extend(txt)

        # this make sure the port types will be avalaible when saved code will run
        lTypes = {}
        lSynonyms = {}
        lPorts = self.inputPorts + self.outputPorts
        for p in lPorts:
            lName = p.datatypeObject.__class__.__name__
            if (lTypes.has_key(lName) is False) and \
               (p.datatypeObject.__module__ != 'NetworkEditor.datatypes'):
                lTypes[lName] = p.datatypeObject.__module__
            lName = p.datatypeObject['name']
            if lSynonyms.has_key(lName) is False:
                lSplitName = lName.split('(')
                lBaseName = lSplitName[0]
                if (len(lSplitName) == 2) and (lSynonyms.has_key(lBaseName) is False):
                    lDict = self.network.getTypeManager().getSynonymDict(lBaseName)
                    if lDict is not None:
                        lSynonyms[lBaseName] = lDict
                lDict = self.network.getTypeManager().getSynonymDict(lName)
                if lDict is not None:
                    lSynonyms[lName] = lDict

        kw['types'] = lTypes
        kw['synonyms'] = lSynonyms
        txt, indent = apply(self.getInitBlock, (className, indent), kw)
        kw.pop('types')
        kw.pop('synonyms')
        lines.extend(txt)

        if dependencies is True:
            nodeName = 'self'
            indent, txt = self.getNodeSourceCodeForNode(self.network,
                                        indent=indent, full=0, nodeName=nodeName)
            lines.extend(txt)

            lines.extend("\n\n" + indent0 + "    " + \
                         "def afterAddingToNetwork(self):\n" + \
                         indent + "pass\n")
            
            constrkw = {}
            constrkw.update( self.constrkw )
            constrkw['name'] = className
            dummyNode = apply( self.originalClass,(),constrkw)
            indent, txt = self.getNodeSourceCodeForPorts(
                self.network, indent=indent,
                ignoreOriginal=False, full=0,
                dummyNode=dummyNode, nodeName=nodeName)
            lines.extend(txt)

            indent, txt = self.getNodeSourceCodeForWidgets(
                self.network, indent=indent,
                ignoreOriginal=False, full=0,
                dummyNode=dummyNode, nodeName=nodeName)
            lines.extend(txt)
        elif dependencies is False:
            txt = self.getComputeFunctionSourceCode(indent=indent)
            lines.extend(txt)

            txt, indent = apply(self.getPortsCreationSourceCode,
                                (self.inputPorts, 'input', indent), kw)
            lines.extend(txt)
            txt, indent = apply(self.getPortsCreationSourceCode,
                                (self.outputPorts, 'output', indent), kw)
            lines.extend(txt)

            txt, indent = self.getWidgetsCreationSourceCode(indent)
            lines.extend(txt)
        else:
            assert(False)

        indent1 = indent + ' '*4

        lines.extend("\n\n" + indent0 + "    " + \
                     "def beforeAddingToNetwork(self, net):\n")

        # this make sure the host web service is loaded
        if self.constrkw.has_key('host'):

            lines.extend( indent + "try:\n" )

            ## get library import cache
            ## then write libray import code
            cache = self.network.buildLibraryImportCache(
                {'files':[]}, self.network, selectedOnly=False)
            li = self.network.getLibraryImportCode(
                     cache, indent1, editor="self.editor",
                     networkName="net",
                     importOnly=True, loadHost=True)
            lines.extend(li)
            lines.extend( indent + "except:\n" + \
                   indent1 + "print 'Warning! Could not load web services'\n\n")

        # this make sure the port widgets will be avalaible when saved code will run
        lines.extend(indent + "try:\n" )

        lWidgetsClass = []
        for p in self.inputPorts:
            lClass = p.widget.__class__
            lModule = lClass.__module__
            if ( lModule != 'NetworkEditor.widgets') \
                and (lModule != '__builtin__') \
                and (lModule not in lWidgetsClass):
                lWidgetsClass.append(lClass)

        lines.append(indent1 + "ed = net.getEditor()\n")
        for w in lWidgetsClass:
            lWidgetsClassName = w.__name__
            lines.append(indent1 + "from %s import %s\n" % (w.__module__, lWidgetsClassName) )
            lines.extend(indent1 + "if %s not in ed.widgetsTable.keys():\n" % lWidgetsClassName )
            lines.extend(indent1 + 4*' ' + \
                         "ed.widgetsTable['%s'] = %s\n" % (lWidgetsClassName, lWidgetsClassName) )

        lines.extend(indent + "except:\n" + \
               indent1 + "import traceback; traceback.print_exc()\n" + \
               indent1 + "print 'Warning! Could not import widgets'\n")

        lines.extend("\n")
        
        return lines

    ####################################################
    #### Helper Methods follow to generate save file ###
    ####################################################

    def getHeaderBlock(self, className, indent="", **kw):
        """Generate source code to import a node from a library or file."""

        lines = []
        
        dependencies = kw['dependencies']
        import datetime
        lNow = datetime.datetime.now().strftime("%A %d %B %Y %H:%M:%S")       
        lCopyright = \
"""########################################################################
#
#    Vision Node - Python source code - file generated by vision
#    %s 
#    
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel Sanner and TSRI
#   
# revision: Guillaume Vareille
#  
#########################################################################
#
# $%s$
#
# $%s$
#

"""%(lNow, "Header:", "Id:") # if directly in the txt, CVS fills these fields

        lines.append(lCopyright)

        return lines, indent


    def getInitBlock(self, className, indent="", **kw):
        """Generate source code to define the __init__() method of the node,
        building the correct constrkw dict, etc."""
        lines = []

        dependencies = kw['dependencies']

        lines.append(indent+"# import node's base class node\n")

#        if dependencies is True:
#            mod = self.originalClass.__module__
#            klass = self.originalClass.__name__
#            txt1 = "from %s import %s\n"%(mod,klass)
#            lines.append(indent+txt1)
#            txt2 = "class %s(%s):\n"%(className,klass)
#            lines.append(indent+txt2)
#        else:
#            txt1 = "from NetworkEditor.items import NetworkNode\n"
#            lines.append(indent+txt1)
#            txt2 = "class %s(NetworkNode):\n"%className
#            lines.append(indent+txt2)

        txt1 = "from NetworkEditor.items import NetworkNode\n"
        lines.append(indent+txt1)
        mod = self.originalClass.__module__
        klass = self.originalClass.__name__
        txt1 = "from %s import %s\n"%(mod,klass)
        lines.append(indent+txt1)
        txt2 = "class %s(%s):\n"%(className,klass)
        lines.append(indent+txt2)

        if self.originalClass.__doc__ is not None:
            lines.append(indent+'    \"\"\"'+self.originalClass.__doc__)
            lines.append('\"\"\"\n')

        indent1 = indent + 4*" "
        indent2 = indent1 + 4*" "
        if kw.has_key('types'):
            lines.append(indent1 + "mRequiredTypes = " + kw['types'].__str__() + '\n')

        if kw.has_key('synonyms'):
            lines.append(indent1 + "mRequiredSynonyms = [\n")
            for lkey, lSynonym in kw['synonyms'].items():
                lines.extend(indent2 + lSynonym.__str__() + ',\n')
            lines.append(indent1 + ']\n')

        # build constructor keyword from original class
        # constrkw is not used by the original class but only by NetworkNode
        constrkw = ''
        for name, value in self.constrkw.items():
            constrkw = constrkw + name+'='+str(value)+', '
        constrkw = constrkw + "constrkw = " + str(self.constrkw)+', '

        indent += 4*" "
        lines.append(indent+\
                  "def __init__(self, %s name='%s', **kw):\n" % (
            constrkw, className))
        indent += 4*" "
                      
        lines.append(indent+"kw['constrkw'] = constrkw\n")
        lines.append(indent+"kw['name'] = name\n")

        if dependencies is True:
            klass = self.originalClass.__name__
            lines.append(indent+"apply(%s.__init__, (self,), kw)\n"%klass)          
            
            # we just fully blank everything an recreate them
            # we will need to save only the differences and not everything
            #lines.append(indent+"self.inputPortsDescr = []\n")
            #lines.append(indent+"self.outputPortsDescr = []\n")
            #lines.append(indent+"self.widgetDescr = {}\n")

            if self._modified is True:
                lines.append(indent+"self.inNodeWidgetsVisibleByDefault = %s\n"%self.inNodeWidgetsVisibleByDefault)

        else:
            lines.append(indent+"apply( NetworkNode.__init__, (self,), kw)\n")
            if self.inNodeWidgetsVisibleByDefault:
                lines.append(indent+"self.inNodeWidgetsVisibleByDefault = True\n")

        return lines, indent


    def getPortsCreationSourceCode(self, ports, ptype='input', indent="",**kw):
        """generates code to create ports using the inputportsDescr and
        outputPortsDescr"""

        lines = []

        dependencies = kw['dependencies']

        assert ptype in ['input', 'output']
        for p in ports:
            d = p.getDescr()
            if d is None:
                d = {}
            lines.append(indent+"self.%sPortsDescr.append(\n"%ptype)
            lines.append(indent+ 4*" " + "%s)\n"%str(d) )
                
        return lines, indent


    def getWidgetsCreationSourceCode(self, indent="",**kw):
        """generating code to create widgets using the widgetDescr"""
        lines = []
        for p in self.inputPorts:
            if p.widget is None:
                continue
            d = p.widget.getDescr()
            # save current widget value
            d['initialValue'] = p.widget.getDataForSaving()
            if d is None:
                d = {}
            lines.append(indent+"self.widgetDescr['%s'] = {\n"%p.name)
            lines.append(indent+ 4*" " + "%s\n"%str(d)[1:] ) #ommit first {

        return lines, indent


    def getComputeFunctionSourceCode(self, indent="", **kw):
        lines = []
        nodeName = 'self'
        lines.append(indent+"code = \"\"\"%s\"\"\"\n"%self.sourceCode)
        lines.append(indent+"%s.configure(function=code)\n"% nodeName)
        return lines


###################### END of methods generating source code ################
#############################################################################


    def outputData(self, **kw):
        for p in self.outputPorts:
            if kw.has_key(p.name):
                data = kw[p.name]
                kw.pop(p.name)
                p.outputData(data)
            else:
                ed = self.getEditor()
                if ed.hasGUI:
                    ed.balloons.tagbind(
                        self.network.canvas, 
                        p.id, 
                        p.balloonBase)
        if len(kw):
            for k in kw.keys():
                warnings.warn( "WARNING: port %s not found in node %s"%(k, self.name) )


    def setFunction(self, source, tagModified=True):
        """Set the node's compute function. If tagModified is True, we set
        _modified=True"""

        self.sourceCode = source
        self.dynamicComputeFunction = self.evalString(source)
        if tagModified:
            self._setModified(True)

        # update the source code editor if available
        if self.objEditor is not None:
            if self.objEditor.funcEditorDialog is not None:
                self.objEditor.funcEditorDialog.settext(source)
                

    def scheduleChildren(self, portList=None):
        """run the children of this node in the same thread as the parent
        if portList is None all children are scheduled, else only
        children of the specified ports are scheduled
"""
        #print "NetworkNodeBase.scheduleChildren"
        net = self.network

        # get the list of nodes to run
        if portList is None:
            allNodes = net.getAllNodes(self.children)
            for n in self.children:
                n.forceExecution = 1
        else:
            children = []
            for p in portList:
                children.extend(map (lambda x: x.node, p.children) )
            for n in children:
                n.forceExecution = 1
            # since a node can be a child through multiple ports we have to
            # make the list of children unique
            allNodes = net.getAllNodes(uniq(children))

        if len(allNodes):
            #self.forceExecution = 1
            #print "SCHEDULE CHILDREN", allNodes
            net.runNodes(allNodes)


    def schedule_cb(self, event=None):
        self.forceExecution = 1
        self.schedule()

        
    def schedule(self):
        """start an execution thread for the subtree under that node
"""
        #print "NetworkNodeBase.schedule", self.network.runOnNewData
        net = self.network
        ed = net.getEditor()
        if ed.hasGUI:
            if hasattr(ed, 'buttonBar'):
                bl = ed.buttonBar.toolbarButtonDict
                if bl.has_key('softrun'):
                    bl['softrun'].disable()
                bl['run'].disable()
                #bl['runWithoutGui'].disable()
                #if ed.withThreads is True:
                bl['pause'].enable()
                bl['stop'].enable()
        net.run([self])


    def computeFunction(self):
        # make sure all required input ports present data
        # make sure data is valid and available
        # call self.dynamicComputeFunction
        # Return 'Go' after successful execution or 'Stop' otherwise

        for p in self.outputPorts:
            if p.dataView:
                p.clearDataView()

        if not self.dynamicComputeFunction:
            return 'Stop'
        lArgs = [self,]

        ed = self.getEditor()
        # for each input port of this node
        newData = 0
        for port in self.inputPorts:

            # this make sure the text entries are used even if the user hasn't pressed return
            if ed.hasGUI and port.widget is not None:
                w = port.widget.widget
                if   isinstance(w, Tkinter.Entry) \
                  or isinstance(w, Pmw.ComboBox):
                    before = port.widget.lastUsedValue    
                    after = port.widget.widget.get()
                    if before != after:
                        port.widget._newdata = True
                
            if port.hasNewData():
                newData = 1
            data = port.getData() # returns 'Stop' if bad or missing data
            if type(data) is types.StringType:
                if data.lower()=='stop':
                    # turn node outline to missing data color
                    if ed.hasGUI and ed.flashNodesWhenRun:
                        c = self.iconMaster
                        c.tk.call((c._w, 'itemconfigure', self.innerBox,
                                   '-outline', '#ff6b00', '-width', 4))
                    return 'Stop'
            if port.dataView:
                port.updateDataView()

            # update Data Browser GUI (only if window is not deiconified)
            if port.objectBrowser and \
               port.objectBrowser.root.state()=='normal':
                port.objectBrowser.root.after(
                    100, port.objectBrowser.refresh_cb )

            lArgs.append(data)

        stat = 'Stop'
        if newData \
          or self.forceExecution \
          or (self.network and self.network.forceExecution):
            #print "running %s with:"%self.name, args
            lCurrentDir = os.getcwd()
            if self.network:
                if self.network.filename is not None:
                    lNetworkDir = os.path.dirname(self.network.filename)
                elif hasattr(self.network, 'macroNode') \
                  and self.network.macroNode.network.filename is not None:
                    lNetworkDir = os.path.dirname(self.network.macroNode.network.filename)
                else:
                    import Vision
                    if hasattr(Vision, 'networkDefaultDirectory'):
                        lNetworkDir = Vision.networkDefaultDirectory
                    else:
                        lNetworkDir = '.'

                # MS WHY do we have to go there ? Oct 2010
                # removed it because this prevented networks from .psf file
                # wfrom working as the tmp dir was deleted
                #if os.path.exists(lNetworkDir):
                    os.chdir(lNetworkDir)
            try:
                stat = apply( self.dynamicComputeFunction, tuple(lArgs) )
            finally:
                os.chdir(lCurrentDir)
            if stat is None:
                stat = 'Go'
            for p in self.outputPorts:
                # update Data Viewer GUI
                if p.dataView:
                    p.updateDataView()
                # update Data Browser GUI (only if window is not deiconified)
                if p.objectBrowser and p.objectBrowser.root.state() =='normal':
                    p.objectBrowser.root.after(
                        100, p.objectBrowser.refresh_cb )
                    
            for p in self.inputPorts:
                p.releaseData()

        return stat
 

    def growRight(self, id, dx):
        """Expand (and shrink) the x-dimension of the node icon to (and from)
        the right."""
        # we get the coords
        coords = self.iconMaster.coords(id)
        # compute the middle point using the bounding box of this object
        bbox = self.iconMaster.bbox(id)
        xmid = (bbox[0] + bbox[2]) * 0.5
        # add dx for every x coord right of the middle point
        for i in range(0,len(coords),2):
            if coords[i]>xmid:
                coords[i]=coords[i]+dx
        apply( self.iconMaster.coords, (id,)+tuple(coords) )


    def growDown(self, id, dy):
        """Expand (and shrink) the y-dimension of the node icon to (and from)
        the top."""
         # we get the coords
        coords = self.iconMaster.coords(id)
        # compute the middle point using the bounding box of this object
        bbox = self.iconMaster.bbox(id)
        ymid = (bbox[1] + bbox[3]) * 0.5
        # add dy for every y coord below of the middle point
        for i in range(1,len(coords),2):
            if coords[i]>ymid:
                coords[i]=coords[i]+dy
        apply( self.iconMaster.coords, (id,)+tuple(coords) )

    
    def updateCode(self, port='ip', action=None, tagModified=True, **kw):
        """update signature of compute function in source code.
We re-write the first line with all port names as arguments.
**kw are not used but allow to match updateCode signature of output ports
"""
        code = self.sourceCode
        # handle input port
        if port == 'ip':
            if action=='add' or action=='remove' or action=='create':
                ## This was bas: 13 assumed that was no space between doit( and
                ## self.  If there is a space we lost the f at the end of self
                #signatureBegin = code.index('def doit(')+13
                signatureBegin = code.index('self')+4
                signatureEnd = code[signatureBegin:].index('):')
                signatureEnd = signatureBegin+signatureEnd
                newCode = code[:signatureBegin]
                if action=='create':
                    for p in self.inputPortsDescr:
                        newCode += ', ' + p['name']
                        #if p['required'] is True:
                        #    newCode += "='NA' "
                        #else:
                        #    newCode += '=None '
                else:
                    for p in self.inputPorts:
                        newCode += ', ' + p.name
                        #if p.required is True:
                        #    newCode += "='NA' "
                        #else:
                        #    newCode += '=None '
                newCode = newCode + code[signatureEnd:]
            elif action=='rename':
                newname = kw['newname']
                oldname = kw['oldname']
                newCode = code.replace(oldname, newname)

        # handle output port
        elif port == 'op':
            newname = kw['newname']
            if action==None:
                return
            if action=='add':
                # add comment on how to output data
                olds = "## to ouput data on port %s use\n"%newname
                olds += "## self.outputData(%s=data)\n"%newname
                code += olds
            elif action=='remove':
                oldname = kw['oldname']
                # remove comment on how to output data
                olds = "## to ouput data on port %s use\n"%oldname
                olds += "## self.outputData(%s=data)\n"%oldname
                code = code.replace(olds, '')
            elif action=='rename':
                oldname = kw['oldname']
                olds = "## to ouput data on port %s use\n"%oldname
                olds += "## self.outputData(%s=data)\n"%oldname
                news = "## to ouput data on port %s use\n"%newname
                news += "## self.outputData(%s=data)\n"%newname
                code = code.replace(olds, news)
            else:
                raise ValueError (
                    "action should be either 'add', 'remove', 'rename', got ",
                    action)
            newCode = code

        else:
            warnings.warn("Wrong port type specified!", stacklevel=2)
            return

        # finally, set the new code
        self.setFunction(newCode, tagModified=tagModified)


    def toggleNodeExpand_cb(self, event=None):
        widgetsInNode = self.getWidgetsForMaster('Node')
        if len(widgetsInNode)==0:
            widgetsInParamPanel = self.getWidgetsForMaster('ParamPanel')
            if len(widgetsInParamPanel):
                if self.paramPanel.master.winfo_ismapped() == 1:
                    self.paramPanel.hide()
                    self.paramPanelTk.set(0)
                else:
                    self.paramPanel.show()
                    self.paramPanelTk.set(1)
        else:
            if self.isExpanded():
                self.expandedIcon = False
                self.hideInNodeWidgets()
            
            else:
                self.expandedIcon = True
                self.showInNodeWidgets()
        self._setModified(True)
                

    def getWidthForPorts(self, maxi=None):
        # compute the width in the icon required for input and output ports
        # if maxw is not none, the maximum is return
        if maxi is None:
            maxi = maxwidth = 0
        # find last visible inputport
        if len(self.inputPorts):
            for p in self.inputPorts[::-1]: # going backwards
                if p.visible:
                    break
            maxwidth = p.relposx+2*p.halfPortWidth
        if len(self.outputPorts):
            for p in self.outputPorts[::-1]: # going backwards
                if p.visible:
                    break
            if p.relposx+2*p.halfPortWidth > maxwidth:
                maxwidth = p.relposx+2*p.halfPortWidth
        return max(maxi, int(round(maxwidth*self.scaleSum)))
                

    def getHeightForPorts(self, maxi=None):
        # compute the height in the icon required for input and output ports
        # if maxw is not none, the maximum is return
        maxheight = 0
        if maxi is None:
            maxi = 0
        # find last visible inputport
        if len(self.inputPorts):
            for p in self.inputPorts[::-1]: # going backwards
                if p.visible:
                    break
            maxheight = p.relposy+2*p.halfPortHeight
        if len(self.outputPorts):
            for p in self.outputPorts[::-1]: # going backwards
                if p.visible:
                    break
            if p.relposy+2*p.halfPortHeight > maxheight:
                maxheight = p.relposy+2*p.halfPortHeight
        return max(maxi, int(round(maxheight*self.scaleSum)))

    
    def getWidthForLabel(self, maxi=None):
        # compute the width in the icon required for the label
        # if maxis is not not, the maximum is return
        if maxi is None:
            maxi = 0
        bb = self.iconMaster.bbox(self.textId)
        return max(maxi, 10+(bb[2]-bb[0]) )  # label has 2*5 padding


    def getWidthForNodeWidgets(self,  maxi=None):
        # compute the width in the icon required for node widgets
        # if maxis is not not, the maximum is return
        if maxi is None:
            maxi = 0

        if self.isExpanded():
            return max(maxi, self.nodeWidgetMaster.winfo_reqwidth()+10)
        else:
            return maxi

    
    def autoResizeX(self):
        # we find how wide the innerBox has to be
        canvas = self.iconMaster
        neededWidth = self.getWidthForPorts()
        neededWidth = self.getWidthForLabel(neededWidth)
        neededWidth = self.getWidthForNodeWidgets(neededWidth)
        # get width of current innerbox
        bb = canvas.bbox(self.innerBox)
        w = bb[2]-bb[0]
        self.resizeIcon(dx=neededWidth-w)


    def autoResizeY(self):
        canvas = self.iconMaster
        bb = canvas.bbox(self.textId)
        labelH = 12+self.progBarH+(bb[3]-bb[1])  # label has 2*5 padding
        if self.isExpanded():
            widgetH = self.nodeWidgetMaster.winfo_reqheight()
            if len(self.getWidgetsForMaster('Node')):
                labelH += 6
        else:
            widgetH = 0
        bb = canvas.bbox(self.innerBox)
        curh = bb[3]-bb[1]

        self.resizeIcon(dy=labelH+widgetH-curh)


    def autoResize(self):
        self.autoResizeX()
        self.autoResizeY()
        if len(self.getWidgetsForMaster('node')):
            # resize gets the right size but always grows to the right
            # by hiding and showing the widgets in node we fix this
            self.toggleNodeExpand_cb()
            self.toggleNodeExpand_cb()


    def getSize(self):
        """returns size of this node as a tuple of (width, height) in pixels"""
        bbox = self.iconMaster.bbox(self.outerBox)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return (w, h)
        

    def hideInNodeWidgets(self, rescale=1):
        # hide widgets in node by destroying canvas object holding them
        # the NE widget is not destroyed
        canvas = self.iconMaster
        if rescale:
            self.autoResizeX()
            h = self.nodeWidgetMaster.winfo_reqheight()
            self.resizeIcon(dy=-h-6)
            #bb = canvas.bbox(self.nodeWidgetTkId)
            #self.resizeIcon(dy=bb[1]-bb[3])
        canvas.delete(self.nodeWidgetTkId)


    def showInNodeWidgets(self, rescale=1):
        canvas = self.iconMaster
        widgetFrame = self.nodeWidgetMaster
        
        oldbb = canvas.bbox(self.innerBox)# find current bbox
        #if len(self.nodeWidgetsID):
        #    bb = canvas.bbox(self.nodeWidgetsID[-1]) # find bbox of last widget
        #else:
        #    bb = canvas.bbox(self.textId) # find bbox of text
        bb = canvas.bbox(self.textId) # find bbox of text

        # pack the frame containg the widgets so we can measure it's size
        widgetFrame.pack()
        canvas.update_idletasks()
        h = widgetFrame.winfo_reqheight() # before asking for its size
        w = widgetFrame.winfo_reqwidth()

## FIXME the frame is created with a given size. Since it is on a canvas
## it does not resize when widgets are added or removed
##         newh =0 
##         for p in self.inputPorts:
##             if p.widget and p.widget.inNode:
##                 newh += p.widget.widgetFrame.winfo_reqheight()
##         h = newh-h
        
        tags = (self.iconTag, 'node')
        # compute center (x,y) of canvas window
        # add a window below text for widgets
        self.nodeWidgetTkId = widgetWin = canvas.create_window(
            bb[0]+(w/2), bb[3]+ self.progBarH +(h/2),
            tags=tags, window=widgetFrame )
        if self.selected:
            canvas.addtag_withtag('selected', widgetWin)

        if rescale:
            self.autoResizeX()
            self.resizeIcon(dy=h+6)


    def getWidgetsForMaster(self, masterName):
        """Return a dict of all widgets bound for a given master in a given
        node (self). Masters can be 'Node' or 'ParamPanel'.
        key is an instance of the port, value is an instance of the widget"""
        
        widgets = {}
        for k, v in self.widgetDescr.items():
            master = v.get('master', 'ParamPanel')
            if master.lower()==masterName.lower():
                # find corresponding widget to this port
                for port in self.inputPorts:
                    if port.name == k:
                        widget = port.widget
                        break
                widgets[port] = widget
        return widgets


    def drawMapIcon(self, naviMap):
        canvas = naviMap.mapCanvas
        x0, y0 = naviMap.upperLeft
        scaleFactor = naviMap.scaleFactor
        c = self.network.canvas.bbox(self.iconTag)
        cid = canvas.create_rectangle(
            [x0+c[0]*scaleFactor, y0+c[1]*scaleFactor,
             x0+c[2]*scaleFactor, y0+c[3]*scaleFactor],
            fill='grey50', outline='black', tag=('navimap',))
        self.naviMapID = cid
        return cid
    

    def buildIcons(self, canvas, posx, posy, small=False):
        """Build NODE icon with ports etc
"""
        NetworkItems.buildIcons(self, canvas)
        network = self.network

        self.paramPanelTk = Tkinter.IntVar()  # to toggle Param. Panel
        self.paramPanelTk.set(0)

        # build node's Icon
        ed = self.getEditor()
        if ed.hasGUI:
            self.buildNodeIcon(canvas, posx, posy, small=small)
    
        # instanciate output ports
        for p in self.outputPorts:
            p.buildIcons(resize=False)

        # instanciate input ports
        inNode = 0
        for p in self.inputPorts: # this loop first so all port have halfPortWidth
            p.buildIcons( resize=False )

        for p in self.inputPorts:
            p.createWidget()
            if p.widget is not None:
                inNode = max(inNode, p.widget.inNode)

        if ed.hasGUI:
            self.autoResizeX() # in case we added too many ports

            # at least one widget is in the node. We show it if visible by default
            if inNode:
                if self.inNodeWidgetsVisibleByDefault:
                    self.expandedIcon = True
                    self.showInNodeWidgets( rescale=1 )

        # instanciate special input ports
        for ip in self.specialInputPorts:
            ip.buildIcons(resize=False)
            if not self.specialPortsVisible:
                ip.deleteIcon()
                
        # instanciate special output ports
        for op in self.specialOutputPorts:
            op.buildIcons(resize=False)
            if not self.specialPortsVisible:
                op.deleteIcon()

        # this is needed because only now do we know the true relposx of ports
        # if we do not do this here, some port icons might be outside the node
        # but we do not want to autoResize() because that would rebuild widgets
        if ed.hasGUI:
            self.autoResizeX()

            # add command entries to node's pull down
            self.menu.add_command(label='Run', command=self.schedule_cb, underline=0)
            self.menu.add_checkbutton(label="Frozen",
                                      variable = self.frozenTk,
                                      command=self.toggleFrozen_cb,
                                      underline=0)
            #        self.menu.add_command(label='Freeze', command=self.toggleFreeze)
            self.menu.add_separator()
            self.menu.add_command(label='Edit', command=self.edit, underline=0)
            self.menu.add_command(label='Edit compute function',
                                  command=self.editComputeFunction_cb,
                                  underline=14)
            self.menu.add_command(label='Introspect',
                                  command=self.introspect,
                                  underline=0)

            self.menu.add_checkbutton(label="Parameter Panel",
                                      variable = self.paramPanelTk,
                                      command=self.toggleParamPanel_cb,
                                      underline=0)
            
            self.menu.add_separator()
            self.menu.add_command(label='Copy', command=self.copy_cb, underline=0)
            self.menu.add_command(label='Cut', command=self.cut_cb, underline=0)
            self.menu.add_command(label='Delete', command=self.delete_cb, underline=0)
            self.menu.add_command(label='Reset', command=self.replaceWith, underline=0)

            if self.__class__ is FunctionNode and hasattr(self.function, 'serviceName'):
                def buildhostCascadeMenu():
                    self.menu.cascadeMenu.delete(0, 'end')
                    for lKey in self.library.libraryDescr.keys():
                        if lKey.startswith('http://') and lKey != suppressMultipleQuotes(self.constrkw['host']):
                            cb = CallBackFunction( self.replaceWithHost, host=lKey)
                            self.menu.cascadeMenu.add_command(label=lKey, command=cb)
                self.menu.cascadeMenu = Tkinter.Menu(self.menu, tearoff=0, postcommand=buildhostCascadeMenu)
                self.menu.add_cascade(label='Replace with node from', menu=self.menu.cascadeMenu)

            if self.specialPortsVisible:
                self.menu.add_command(label='Hide special ports',
                                      command=self.hideSpecialPorts,
                                      underline=5)
            else:
                self.menu.add_command(label='Show special ports',
                                      command=self.showSpecialPorts,
                                      underline=5)

    def delete(self):

        # remove all connections to this node
        inConnections = self.getInConnections()
        self.network.deleteConnections(inConnections, 0, schedule=False)
        outConnections = self.getOutConnections()
        self.network.deleteConnections(outConnections, 0)

        self.beforeRemovingFromNetwork()

        # delete this node's ports
        inNode = 0
        for p in self.inputPorts[:]: # IMPORTANT NOTE: since we will delete
            # the port from self.inputPorts while we are looping over this
            # list, we need to loop over a copy to avoid unpredictable
            # results!
            if p.dataView is not None: # kill data viewer window
                p.dataView.destroy()
            if p.widget:
                # close widget editor
                if p.widget.objEditor:
                    p.widget.objEditor.Cancel_cb()
                inNode = max(0, p.widget.inNode)
            # close port editor
            if p.objEditor:
                p.objEditor.Cancel()
            self.deletePort(p, resize=False, updateSignature=False)

        for p in self.outputPorts[:]:
            if p.dataView is not None: # kill data viewer window
                p.dataView.destroy()
            if p.objEditor:
                p.objEditor.Cancel()
            self.deletePort(p, resize=False, updateSignature=False)

        for p in self.specialInputPorts[:]:
            self.deletePort(p, resize=False, updateSignature=False)

        for p in self.specialOutputPorts[:]:
            self.deletePort(p, resize=False, updateSignature=False)

        # delete the node's param. panel
        self.paramPanel.destroy()


        if self.objEditor:
            self.objEditor.Dismiss()

        if self.isExpanded() and inNode:
            self.hideInNodeWidgets( )

        self.deleteIcon()
        self.afterRemovingFromNetwork()


    def addSaveNodeMenuEntries(self):
        """add 'save source code' and 'add to library' entries to node menu'"""

        if self.readOnly:
            return
        
        try:
            self.menu.index('Save as customized node')
        except:
            self.menu.add_separator()
            funcDependent = CallBackFunction(self.saveSource_cb, True)
            funcIndependent = CallBackFunction(self.saveSource_cb, False)
            if hasattr(self, 'geoms') is False: 
                if issubclass(self.__class__, FunctionNode):
                    pass
                    # still in devellopment:
                    #self.menu.add_command(
                    #            label='Save as customized node inheriting',
                    #            command=funcDependent)
                else:
                    self.menu.add_command(
                                label='Save as customized node',
                                command=funcIndependent)

    ## PLEASE NOTE: This will be enabled in a future release of Vision
##             ed = self.network.getEditor()
##             if hasattr(ed, 'addNodeToLibrary'):
##                 fun = CallBackFunction( ed.addNodeToLibrary, self)
##                 self.menu.add_command(label='add to library', command=fun)


    def copy_cb(self, event=None):
        ed = self.network.getEditor()
        self.network.selectNodes([self])
        ed.copyNetwork_cb(event)


    def cut_cb(self, event=None):
        ed = self.network.getEditor()
        self.network.selectNodes([self])
        ed.cutNetwork_cb(event)


    def delete_cb(self, event=None):
        self.network.selectNodes([self])
        nodeList = self.network.selectedNodes[:]
        self.network.deleteNodes(nodeList)


    def edit(self, event=None):
        if self.objEditor:
            self.objEditor.top.master.lift()
            return
        self.objEditor = NodeEditor(self)


    def editComputeFunction_cb(self, event=None):
        if not self.objEditor:
            self.objEditor = NodeEditor(self)

        self.objEditor.editButton.invoke()
            
    
    def evalString(self, str):
        if not str: return
        try:
            function = eval("%s"%str)
        except:
            #try:
                obj = compile(str, '<string>', 'exec')
                if self.__module__ == '__main__':
                    d = globals()
                else:
                    # import the module from which this node comes
                    mn = self.__module__
                    m = __import__(mn)
                    # get the global dictionary of this module
                    ind = string.find(mn, '.')
                    if ind==-1: # not '.' was found
                        d = eval('m'+'.__dict__')
                    else:
                        d = eval('m'+mn[ind:]+'.__dict__')
                # use the module's dictionary as global scope
                exec(obj, d)
                # when a function has names arguments it seems that the
                # co_names is (None, 'functionName')
                if len(obj.co_names)==0:
                    function = None
                else:
                    function = eval(obj.co_names[-1], d)
            #except:
            #    raise ValueError
        return function


    def move(self, dx, dy, absolute=True, tagModified=True):
        """if absolute is set to False, the node moves about the increment
        dx,dy. If absolute is True, the node moves to the position dx,dy
        Connections are updated automatically."""

        if self.editor.hasGUI:
            self.network.moveSubGraph([self], dx, dy, absolute=absolute,
                                      tagModified=tagModified)


    def getSourceCode(self):
        # this method is implemented in subclasses
        # create the source code to rebuild this object
        # used for saving or copying
        pass


    def toggleParamPanel_cb(self, event=None):
        if self.paramPanel.master.winfo_ismapped() == 0:
            self.paramPanel.show()
            self.showParams_cb()
        else:
            self.paramPanel.hide()


    def ensureRootNode(self):
        # count parent to decide whether or not second node is a root
        lInConnections = self.getInConnections()
        if len(lInConnections) == 0:
            self.isRootNode = 1
            if self not in self.network.rootNodes:
                self.network.rootNodes.append(self)
        else:
            for lConn in lInConnections:
                if lConn.blocking is True:
                    if self in self.network.rootNodes:
                        self.network.rootNodes.remove(self)
                    break;
            else: # we didn't break
                # all the connections are not blocking
                self.isRootNode = 1
                if self not in self.network.rootNodes:
                    self.network.rootNodes.append(self)



class NetworkNode(NetworkNodeBase):
    """This class implements a node that is represented using a Polygon
    """

    def __init__(self, name='NoName', sourceCode=None, originalClass=None,
                 constrkw=None, library=None, progbar=0, **kw):

        apply( NetworkNodeBase.__init__,
               (self, name, sourceCode, originalClass, constrkw, library,
                progbar), kw)
        
        self.highlightOptions = {'highlightbackground':'red'}
        self.unhighlightOptions = {'highlightbackground':'gray50'}
        self.selectOptions = {'fill':'yellow'}
        self.deselectOptions = {'fill':'gray85'}
        self.inNodeWidgetsVisibleByDefault = True

        self.inputPortByName = {}
        self.outputPortByName = {}


    def replaceWithHost(self, klass=None, library=None, host='http://krusty.ucsd.edu:8081/opal2'):
        """a function to replace a node with another node. the connections are recreated.
the connected ports must have the same name in the new node and in the original node.
"""
        #print "replaceWithHost", self, host

        constrkw = copy.deepcopy(self.constrkw)
        if library is None:
            library = self.library
        if library is not None:
            constrkw['library'] = library
        if klass is None:
            klass = self.__class__
        constrkw['klass'] = klass    

        if klass is FunctionNode \
          and hasattr(self.function, 'serviceName') \
          and host is not None:
            constrkw['host'] = suppressMultipleQuotes(host)
            serverName = host.split('http://')[-1]
            serverName = serverName.split('/')[0]
            serverName = serverName.split(':')[0]
            serverName = serverName.replace('.','_')
            
            # to replace exactly with the same one
            #constrkw['functionOrString'] = \
            #         self.function.serviceOriginalName.lower() + '_' + serverName
            
            # to pick any better version
            if self.library.libraryDescr.has_key(host):
                lversion = 0 # replace with the highest version available on the host
                #lversion = self.function.version # replace only if version is at least equal to current
                # to eval we need to bring the main scope into this local scope
                from mglutil.util.misc import importMainOrIPythonMain
                lMainDict = importMainOrIPythonMain()
                for modItemName in set(lMainDict).difference(dir()):
                    locals()[modItemName] = lMainDict[modItemName]
                del constrkw['functionOrString']
                for node in self.library.libraryDescr[host]['nodes']:
                    try:
                        lFunction = eval(node.kw['functionOrString'])
                        if lFunction.serviceName == self.function.serviceName \
                          and lFunction.version >= lversion:
                            constrkw['functionOrString'] = lFunction.serviceOriginalName + '_' + serverName
                    except:
                        pass
        if constrkw.has_key('functionOrString'):
            return apply(self.replaceWith, (), constrkw)
        else:
            return False


    def replaceWith(self, klass=None, **kw):
        """a function to replace a node with another node. the connections are recreated.
the connected ports must have the same name in the new node and in the original node.
"""
        if len(kw) == 0:
            kw = copy.deepcopy(self.constrkw)
        if kw.has_key('library') is False:
            kw['library'] = self.library
        if klass is None:
            klass = self.__class__

        try:
            lNewNode = apply(klass,(),kw)
            lNewNode.inNodeWidgetsVisibleByDefault = self.expandedIcon #by default we want the new node to be in the same state as the curren one
            self.network.addNode(lNewNode, posx=self.posx, posy=self.posy)
            if self.specialPortsVisible is True:
                self.showSpecialPorts()

            lFailure = False
            for port in self.inputPorts:
                if lFailure is False:
                    for connection in port.connections:
                        if lFailure is False:
                            try:
                                self.network.connectNodes(
                                    connection.port1.node, lNewNode,
                                    connection.port1.name, port.name,
                                    blocking=connection.blocking )
                            except:
                                lFailure = True

            for port in self.inputPorts:
                if port.widget is not None:
                    try:
                        lNewNode.inputPortByName[port.name].widget.set(port.widget.get())
                    except:
                        pass

            lDownstreamNodeInputPortSingleConnection = {}
            if lFailure is False:
                for port in self.outputPorts:
                    if lFailure is False:
                        # input ports downstream have to accept multiple connections otherwise they can't be connected
                        for connection in port.connections:
                            lDownstreamNodeInputPortSingleConnection[connection.port2.node] = \
                                                               (connection.port2.name,
                                                                connection.port2.singleConnection)
                            connection.port2.singleConnection = 'multiple'
                            try:
                                self.network.connectNodes(
                                    lNewNode, connection.port2.node,
                                    port.name, connection.port2.name,
                                    blocking=connection.blocking )
                            except:
                                lFailure = True
                # input ports downstream are set back to what they were
                for lNode, portNameSingleConnection in lDownstreamNodeInputPortSingleConnection.items():
                    lNode.inputPortByName[portNameSingleConnection[0]].singleConnection = portNameSingleConnection[1]

            if lFailure is False:
                self.network.deleteNodes([self])
                #print "replaced"
                return True
            else:
                self.network.deleteNodes([lNewNode])

        except Exception, e:
            print e
            #warnings.warn( str(e) )

        return False


    def createPorts(self):
        for kw in self.outputPortsDescr:
            kw['updateSignature'] = False # prevent recreating source code sig.
            op = self.addOutputPort(**kw)

        # create all inputPorts from description
        for kw in self.inputPortsDescr:
            kw['updateSignature'] = False # prevent recreating source code sig.
            ip = self.addInputPort(**kw)
            # create widgets
            ip.createWidget()


        # create all specialPorts
        self.addSpecialPorts()

    def isExpanded(self):
        """returns True if widgets inside the node as displayed"""
        return self.expandedIcon


    def editorVisible(self):
        """returns True if the node Editor is visible"""
        return self.objEditor is not None


    def getColor(self):
        if self.iconMaster is None: return
        return self.iconMaster.itemconfigure(self.innerBox)['fill'][-1]


    def setColor(self, color):
        ## FOR unknown reasons c.tk.call((c._w, 'itemcget', self.innerBox, '-fill') can return 'None' sometimes on SGI when using threads
        c = self.iconMaster
        if c is None:
            print 'Canvas is None'
            return 
        oldCol = c.tk.call((c._w, 'itemcget', self.innerBox, '-fill') )
        while oldCol=='None':
            print "//////////////////////////", oldCol,self.innerBox, c 
            oldCol = c.tk.call((c._w, 'itemcget', self.innerBox, '-fill') )
            print "\\\\\\\\\\\\\\\\\\\\\\",oldCol,self.innerBox, c 
        #oldCol = c.itemconfigure(self.innerBox)['fill'][-1]
        c.tk.call((c._w, 'itemconfigure', self.innerBox, '-fill', color))
        #c.itemconfigure(self.innerBox, fill=color)
        return oldCol

## OBSOLETE was used for nodes that were widgets
##
##      def highlight(self, event=None):
##          if self.iconMaster is None: return
##          apply( self.iconMaster.itemconfigure, (self.innerBox,),
##                 self.highlightOptions )


##      def unhighlight(self, event=None):
##          if self.iconMaster is None: return
##          apply( self.iconMaster.itemconfigure, (self.innerBox,),
##                 self.unhighlightOptions )


    def getFont(self):
        if self.iconMaster is None:
            return
        return self.iconMaster.itemconfigure(self.textId)['font'][-1]
        

    def setFont(self, font):
        # has to be a tuple like this: (ensureFontCase('helvetica'),'-12','bold')
        if self.iconMaster is None:
            return
        assert font is not None and len(font)
        font = tuple(font)
        self.iconMaster.itemconfig(self.textId, font=font)
        

    def select(self):
        NetworkItems.select(self)
        if self.iconMaster is None: return
        apply( self.iconMaster.itemconfigure, (self.innerBox,),
               self.selectOptions )
    

    def deselect(self):
        NetworkItems.deselect(self)
        if self.iconMaster is None: return
        apply( self.iconMaster.itemconfigure, (self.innerBox,),
               self.deselectOptions )


    def resizeIcon(self, dx=0, dy=0):
        if dx:
            self.growRight(self.innerBox, dx)
            self.growRight(self.outerBox, dx)
            self.growRight(self.lowerLine, dx)
            self.growRight(self.upperLine, dx)

            # move the special outputPort icons if visible
            if self.specialPortsVisible:
                for p in self.specialOutputPorts:
                    p.deleteIcon()
                    p.createIcon()

        if dy:
            self.growDown(self.innerBox, dy)
            self.growDown(self.outerBox, dy)
            self.growDown(self.lowerLine, dy)
            self.growDown(self.upperLine, dy)
            for p in self.outputPorts:
                p.relposy = p.relposy + dy
                p.deleteIcon()
                p.createIcon()
                for c in p.connections:
                    if c.id:
                        c.updatePosition()


    def addInputPort(self, name=None, updateSignature=True,
                     _previousWidgetDescr=None, **kw):
        #             ):
        defaults = {
            'balloon':None, '_previousWidgetDescr':None,
            'required':True, 'datatype':'None', 'width':None, 'height':None,
            'singleConnection':True, 
            'beforeConnect':None, 'afterConnect':None,
            'beforeDisconnect':None, 'afterDisconnect':None,
            'shape':None, 'color':None, 'cast':True,
            'originalDatatype':None, 'defaultValue':None,
            'inputPortClass':InputPort,
            }
        defaults.update(kw)
        kw = defaults
        """Create input port and creates icon
NOTE: this method does not update the description"""

        number = len(self.inputPorts)
        if name is None:
            name = 'in'+str(number)

        # create unique name
        portNames = []
        for p in self.inputPorts:
            portNames.append(p.name)

        if name in portNames:
            i = number
            while (True):
                newname = name+str(i)
                if newname not in portNames:
                    break
                i = i+1
            name = newname

        # create port
        inputPortClass = kw.pop('inputPortClass', InputPort)
        #print 'ADD INPUT PORT', self.name, inputPortClass, kw
        ip = inputPortClass( name, self, **kw)
#            name, self, datatype, required, balloon, width, height, 
#            singleConnection, beforeConnect, afterConnect, beforeDisconnect,
#            afterDisconnect, shape, color, cast=cast,
#            originalDatatype=originalDatatype,
#            defaultValue=defaultValue, **kw
#            )
        self.inputPorts.append(ip)
        if self.iconMaster:
            ip.buildIcons()

        if not self.getEditor().hasGUI:
            ip.createWidget() # create NGWidget

        # and add descr to node.inputPortsDescr if it does not exist
        pdescr = self.inputPortsDescr
        found = False
        for d in pdescr:
            if d['name'] == name:
                found = True
                break
        if not found:
            descr = {'name':name, 'datatype':kw['datatype'],
                     'required':kw['required'], 'balloon':kw['balloon'],
                     'singleConnection':kw['singleConnection']}
            self.inputPortsDescr.append(descr)

        if _previousWidgetDescr is not None:
            ip.previousWidgetDescr = _previousWidgetDescr

        # generate unique number, which is used for saving/restoring
        ip._id = self._inputPortsID
        self._inputPortsID += 1

        ip._setModified(True)
        ip._setOriginal(False)

        # change signature of compute function
        if updateSignature is True:
            self.updateCode(port='ip', action='add', tagModified=False)

        self.inputPortByName[name] = ip

        return ip


    def refreshInputPortData(self):
        d = {}
        for p in self.inputPorts:
            d[p.name] = p.getData()
        return d


    def addOutputPort(self, name=None, updateSignature=True,
                      **kw):
        defaults = {'datatype':'None', 'width':None,
                    'height':None, 'balloon':None, 
                    'beforeConnect':None, 'afterConnect':None,
                    'beforeDisconnect':None, 'afterDisconnect':None,
                    'shape':None, 'color':None}
        defaults.update(kw)
        kw = defaults
        """Create output port and creates icon
NOTE: this method does not update the description nor the function's signature"""
        number = len(self.outputPorts)
        if name is None:
            name = 'out'+str(number)

        # create unique name
        portNames = []
        for p in self.outputPorts:
            portNames.append(p.name)

        if name in portNames:
            i = number
            while (True):
                newname = name+str(i)
                if newname not in portNames:
                    break
            i = i+1
            name = newname

        # create port    
        outputPortClass = kw.pop('outputPortClass', OutputPort)
        op = outputPortClass(name, self, **kw)
                        #datatype, balloon, width, height,
                        #beforeConnect, afterConnect, beforeDisconnect,
                        #afterDisconnect)
        
        self.outputPorts.append(op)
        if self.iconMaster:
            op.buildIcons()

        # and add descr to node.outputPortsDescr if it does not exist
        pdescr = self.outputPortsDescr
        found = False
        for d in pdescr:
            if d['name'] == name:
                found = True
                break
        if not found:
            descr = {'name':name, 'datatype':kw['datatype'],
                     'balloon':kw['balloon']}
            self.outputPortsDescr.append(descr)

        # generate unique number, which is used for saving/restoring
        op._id = self._outputPortsID
        self._outputPortsID += 1

        op._setModified(True)
        op._setOriginal(False)

        # add comment to code on how to output data on that port
        if updateSignature is True:
            self.updateCode(port='op', action='add', newname=op.name, tagModified=False)

        self.outputPortByName[name] = op
        
        return op


    def deletePort(self, p, resize=True, updateSignature=True):
        NetworkItems.deletePort(self, p, resize)
        # update code first, then delete
        if updateSignature and isinstance(p, InputPort):
            self.updateCode(port='ip', action='remove', tagModified=False)
            self.inputPortByName.pop(p.name)
        elif updateSignature and isinstance(p, OutputPort):
            self.updateCode(port='op', action='remove', newname='', oldname=p.name, tagModified=False)
            self.outputPortByName.pop(p.name)


    def deletePortByName(self, portName, resize=True, updateSignature=True):
        """delete a port by specifying a port name (port names are unique
within a given node)."""
        port = self.findPortByName()
        self.deletePort(port, resize=resize, updateSignature=updateSignature)
        
            

    def showSpecialPorts(self, tagModified=True, event=None):
        self.specialPortsVisible = True
        self._setModified(tagModified)
        for p in self.specialOutputPorts:
            p.createIcon()
        for p in self.specialInputPorts:
            p.createIcon()
        self.menu.entryconfigure('Show special ports',
                                 label='Hide special ports',
                                 command=self.hideSpecialPorts)


        
    def hideSpecialPorts(self, tagModified=True, event=None):
        self.specialPortsVisible = False
        self._setModified(tagModified)
        for p in self.specialOutputPorts:
            p.node.network.deleteConnections(p.connections, undo=1)
            p.deleteIcon()
            
        for p in self.specialInputPorts:
            p.node.network.deleteConnections(p.connections, undo=1)
            p.deleteIcon()
        self.menu.entryconfigure('Hide special ports',
                                 label='Show special ports',
                                 command=self.showSpecialPorts)
        
        

    def addSpecialPorts(self):
        """add special ports to special ports list. But do not build icons"""
        # port to receive an impulse that will trigger the execution of the
        # node
        ip = RunNodeInputPort(self)
        ip.network = self.network
        self.specialInputPorts.append( ip )

        # port that always output an impulse upon successful completion
        # of the node's function
        op = TriggerOutputPort(self)
        op.network = self.network
        self.specialOutputPorts.append( op )
        
        ed = self.getEditor()
        ip.vEditor = weakref.ref( ed )
        op.vEditor = weakref.ref( ed )


    def buildSmallIcon(self, canvas, posx, posy, font=None):
        """build node proxy icon (icons in library categories"""
        if font is None:
            font = self.ed.font['LibNodes']
        font = tuple(font)
    
        self.textId = canvas.create_text(
            posx, posy, text=self.name, justify=Tkinter.CENTER,
            anchor='w', tags='node', font=font)
            
        self.iconTag = 'node'+str(self.textId)
        bb = canvas.bbox(self.textId)       

        # adding the self.id as a unique tag for this node
        canvas.addtag_closest(self.iconTag, posx, posy, start=self.textId)

        bdx1 = 2 # x padding around label
        bdy1 = 0 # y padding around label
        bdx2 = bdx1+3 # label padding + relief width
        bdy2 = bdy1+3 # label padding + relief width
        self.innerBox = canvas.create_rectangle(
            bb[0]-bdx1, bb[1]-bdy1, bb[2]+bdx1, bb[3]+bdy1,
            tags=(self.iconTag,'node'), fill='gray85')
        # the innerBox is the canvas item used to designate this node
        self.id = self.innerBox

        # add a shadow below
        if self.library is not None:
            color1 = self.library.color
        else:
            color1 = 'gray95'

        # upper right triangle
        self.upperLine = canvas.create_polygon(
            bb[0]-bdx2, bb[1]-bdy2, bb[0]-bdx1, bb[1]-bdy1,
            bb[2]+bdx1, bb[3]+bdy1, bb[2]+bdx2, bb[3]+bdy2,
            bb[2]+bdx2, bb[1]-bdy2,
            width=4, tags=(self.iconTag,'node'), fill=color1 )
        
        # lower left triangle
        self.lowerLine = canvas.create_polygon(
            bb[0]-bdx2, bb[1]-bdy2, bb[0]-bdx1, bb[1]-bdy1,
            bb[2]+bdx1, bb[3]+bdy1, bb[2]+bdx2, bb[3]+bdy2,
            bb[0]-bdx2, bb[3]+bdy2,
            width=4, tags=(self.iconTag,'node'), fill='gray45' )

        self.outerBox = canvas.create_rectangle(
            bb[0]-bdx2, bb[1]-bdy2, bb[2]+bdx2, bb[3]+bdy2,
            width=1, tags=(self.iconTag,'node'))

        canvas.tag_raise(self.innerBox, self.outerBox)
        canvas.tag_raise(self.textId, self.innerBox)

        return bb


    def deleteSmallIcon(self, canvas, item):
        # Experimental! 
        node = item.dummyNode
        canvas.delete(node.textId)
        canvas.delete(node.innerBox)
        canvas.delete(node.outerBox)
        canvas.delete(node.iconTag)

 
    def buildNodeIcon(self, canvas, posx, posy, small=False):
        # build a frame that will hold all widgets in node
        if hasattr(self.iconMaster,'tk'):
            self.nodeWidgetMaster = Tkinter.Frame(
                self.iconMaster, borderwidth=3, relief='sunken' , bg='#c3d0a6')

        ed = self.getEditor()

        if small is True:
            font = tuple(ed.font['LibNodes'])
            lInner = 2
            lOuter = 4
        else:
            font = tuple(ed.font['Nodes'])
            lInner = 5
            lOuter = 8

        self.textId = canvas.create_text(
            posx, posy, text=self.name, justify=Tkinter.CENTER,
            anchor='w', tags='node', font=font)
        canvas.tag_bind(self.textId, "<Control-ButtonRelease-1>",
                        self.setLabel_cb)

        self.iconTag = 'node'+str(self.textId)

        # add self.iconTag tag to self.textId
        canvas.itemconfig(self.textId, tags=(self.iconTag,'node'))

        bb = canvas.bbox(self.textId)       

##          # NOTE: THIS LINE ADDS RANDOMLY WRONG TAGS TO NODES >>>> COPY/PASTE
##          # WON'T WORK CORRECTLY!!! WITHOUT THIS LINE, EVERYTHING SEEMS TO
##          # WORK FINE.
##          #adding the self.id as a unique tag for this node
##          canvas.addtag_closest(self.iconTag, posx, posy, start=self.textId)

        progBarH = self.progBarH

        # this method is also called by a network refresh, thus we need to
        # get the description of the node and color it accordingly (frozen
        # or colored by node library)
        color = "gray85"  # default color is gray
        if self.editor.colorNodeByLibraryTk.get() == 1:
            if self.library is not None:
                color = self.library.color # color by node library color
        # if node is frozen, this overwrites everything
        if self.frozen:
            color = '#b6d3f6' # color light blue

        self.innerBox = canvas.create_rectangle(
            bb[0]-lInner, bb[1]-lInner, bb[2]+lInner, bb[3]+lInner+progBarH,
            tags=(self.iconTag,'node'), fill=color)#, width=2 )

        # the innerBox is the canvas item used to designate this node
        self.id = self.innerBox
        
        # add a shadow below (color by Library)
        if self.library is not None:
            color1 = self.library.color
        else:
            color1 = 'gray95'

        self.outerBox = canvas.create_rectangle(
            bb[0]-lOuter, bb[1]-lOuter, bb[2]+lOuter, bb[3]+lOuter+progBarH,
            width=1, tags=(self.iconTag,'node'))

        # get a shortcut to the bounding boxes used later on
        ibb = canvas.bbox(self.innerBox) 
        obb = canvas.bbox(self.outerBox)

        # upper right polygon (this is used to color the node icons upper
        # and right side with the corresponding node library color)
        self.upperLine = canvas.create_polygon(
            # note: we have to compensate +1 and -1 because of '1'-based
            # coord system
            obb[0]+1, obb[1]+1, ibb[0]+1, ibb[1]+1,
            ibb[2]-1, ibb[3]-1, obb[2]-1, obb[3]-1, 
            obb[2]-1, obb[1]+1,
            width=4, tags=(self.iconTag,'node'), fill=color1 )

        # lower left polygon (this is used to 'shade' the node icons lower
        # and right side with a dark grey color to give it a 3-D impression
        self.lowerLine = canvas.create_polygon(
            # note: we have to compensate +1 and -1 because of '1'-based
            # coord system
            obb[0]+1, obb[1]+1, ibb[0]+1, ibb[1]+1,
            ibb[2]-1, ibb[3]-1, obb[2]-1, obb[3]-1,
            obb[0]+1, obb[3]-1,
            width=4, tags=(self.iconTag,'node'), fill='gray45' )

        canvas.tag_raise(self.outerBox)
        canvas.tag_raise(self.innerBox, self.outerBox)
        canvas.tag_raise(self.textId, self.innerBox)

        # add the progress bar
        if self.hasProgBar:
            pbid1 = canvas.create_rectangle(
                bb[0]-3, bb[3]-2, bb[2]+3, bb[3]+1+progBarH,
                tags=(self.iconTag,'node'), fill='green')
            self.pbid1 = pbid1

            pbid2 = canvas.create_rectangle(
                bb[2]+3, bb[3]-2, bb[2]+3, bb[3]+1+progBarH,
                {'tags':(self.iconTag,'node'), 'fill':'red'} )
            self.pbid2 = pbid2

        # and set posx, posy
        self.updatePosXPosY(posx, posy)

        if self.network is not None:
            self.move(posx, posy)
        self.hasMoved = False # reset this attribute because the current
                              # position is now the original position


    def setLabel_cb(self, event):
        self._tmproot = root = Tkinter.Toplevel()
        root.transient()
        root.geometry("+%d+%d"%root.winfo_pointerxy())
        root.overrideredirect(True)
        self._tmpEntry = Tkinter.Entry(root)
        self._tmpEntry.pack()
        self._tmpEntry.bind("<Return>", self.setNewLabel_cb)


    def setNewLabel_cb(self, event):
        name = self._tmpEntry.get()
        self.rename(name)
        self._tmpEntry.destroy()
        self._tmproot.destroy()


    def setProgressBar(self, percent):
        """update node's progress bar. percent should be between 0.0 and 1.0"""
        if not self.hasProgBar:
            return
        canvas = self.iconMaster
        c = canvas.coords(self.pbid1)
        c[0] = c[0] + (c[2]-c[0])*percent
        canvas.coords(self.pbid2, c[0], c[1], c[2], c[3])
        

    def updatePosXPosY(self, dx=None, dy=None):
        """set node.posx and node.posy after node has been moved"""
        bbox = self.iconMaster.bbox(self.outerBox)
        self.posx = bbox[0]
        self.posy = bbox[1]


    def setModifiedTag(self):
        """THIS METHOD REMAINS FOR BACKWARDS COMPATIBILITY WITH OLD NETWORKS!
        Sets self._modified=True"""
        self._setModified(True)
        


class NetworkConnection(NetworkItems):
    """This class implements a connection between nodes, drawing
    lines between the centers of 2 ports.
    The mode can be set to 'straight' or 'angles' to have a straight line or
    lines using only right angles.
    smooth=1 option can be used for splines
    joinstyle = 'bevel', 'miter' and 'round'
    """
    arcNum = 0

    def __init__(self, port1, port2, mode='straight', name=None,
                 blocking=None, smooth=False, splitratio=None,
                 hidden=False, **kw):

        if name is None:
            name = port1.node.name+'('+port1.name+')'+'_'+port2.node.name+'('+port2.name+')'

        if splitratio is None:
            splitratio=[random.uniform(.2,.75), random.uniform(.2,.75)] # was [.5, .5]

        NetworkItems.__init__(self, name)

        self.hidden = hidden
        self.id2 = None
        self.iconTag2 = None

        self.port1 = port1
        self.port2 = port2
        port1.children.append(port2)
        #assert self not in port1.connections
        port1.connections.append(self)
        port1.node.children.append(port2.node)
        port2.parents.append(port1)
        #assert self not in port2.connections
        port2.connections.append(self)
        port2.node.parents.append(port1.node)
        leditor = self.port1.editor

        if blocking is None:
            blocking = leditor.createBlockingConnections
        self.blocking = blocking # when true a child node can not run before 
                                 # the parent node has run

        self.mode = mode
        if leditor is not None and hasattr(leditor, 'splineConnections'):
            self.smooth = leditor.splineConnections
        else:
            self.smooth = smooth
        self.splitratio = copy.deepcopy(splitratio)

        w = self.connectionWidth = 3

        if port1.node.getEditor().hasGUI:
            col = port1.datatypeObject['color']
            if not kw.has_key('arrow'): kw['arrow']='last'
            if not kw.has_key('fill'): kw['fill']=col
            if not kw.has_key('width'): kw['width']=w
            if not kw.has_key('width'): kw['width']=w
            if not kw.has_key('activefill'): kw['activefill']='pink'
            kw['smooth'] = self.smooth

            self.lineOptions = kw
            
            self.highlightOptions = {'fill':'red', 'width':w, 'arrow':'last'}
            self.unhighlightOptions = {'width':w, 'arrow':'last'}
            self.unhighlightOptions['fill'] = col
        
            self.selectOptions = {
                'connection0': {'fill':'blue', 'width':w, 'arrow':'last'},
                'connection1': {'fill':'pink', 'width':w, 'arrow':'last'},
                'connection2': {'fill':'purple', 'width':w, 'arrow':'last'},
                }
            self.deselectOptions = {'width':w, 'arrow':'last'}
            self.deselectOptions['fill'] = col

            self.mouseAction['<Button-1>'] = self.reshapeConnection
            
            self.parentMenu = None

            self.isBlockingTk = Tkinter.IntVar()
            self.isBlockingTk.set(self.blocking)

        if isinstance(port1.node, NetworkNode) and isinstance(port2.node, NetworkNode):
            self._mode = 1
        else:
            self._mode = 2

    def reshapeConnection(self, event):
        # get a handle to the network of this node
        c = self.iconMaster
        # register an additional function to reshape connection
        num = event.num
        # FIXME looks like I am binding this many times !
        c.bind("<B%d-Motion>"%num, self.moveReshape,'+')
        c.bind("<ButtonRelease-%d>"%num, self.moveEndReshape, '+')
        
##     def moveReshape(self, event):
##         c = self.iconMaster
##         y = c.canvasy(event.y)
## 	dy = y - self.network.lasty
##         self.network.lasty = y
##         coords = c.coords(self.iconTag)
##         coords[3] = coords[3]+dy
##         coords[5] = coords[5]+dy
##         apply( c.coords, (self.iconTag,)+tuple(coords) )

##     def moveEndReshape(self, event):
##         c = self.iconMaster
##         num = event.num
##         c.unbind("<B%d-Motion>"%num)
##         c.bind("<ButtonRelease-%d>"%num, self.moveEndReshape, '+')

    
    # patch from Karl Gutwin 2003-03-27 16:05 
    def moveReshape(self, event):
        #print "moveReshape"
        c = self.iconMaster
        y = c.canvasy(event.y)
        x = c.canvasx(event.x)
        dy = y - self.network.lasty
        dx = x - self.network.lastx
        self.network.lasty = y
        self.network.lastx = x
        coords = c.coords(self.iconTag)

        if len(coords)==12:
            coords[4] = coords[4]+dx
            coords[6] = coords[6]+dx
            if y > ((coords[5]+coords[7])/2):
                coords[3] = coords[3]+dy
                coords[5] = coords[5]+dy
            else:
                coords[7] = coords[7]+dy
                coords[9] = coords[9]+dy
        else:
            coords[3] = coords[3]+dy
            coords[5] = coords[5]+dy

        self.calculateNewSplitratio(coords)

        apply( c.coords, (self.iconTag,)+tuple(coords) )


    def calculateNewSplitratio(self, coords):

        self.splitratio[0] = coords[0]-coords[4]
        lDistance = coords[0]-coords[-2]
        if lDistance != 0:
            self.splitratio[0] /= float(lDistance)
        if self.splitratio[0] > 2:
            self.splitratio[0] = 2
        elif self.splitratio[0] < -2:
            self.splitratio[0] = -2

        self.splitratio[1] = coords[1]-coords[5]
        lDistance = coords[1]-coords[-1]
        if lDistance != 0:
            self.splitratio[1] /= float(lDistance)
        if self.splitratio[1] > 2:
            self.splitratio[1] = 2
        elif self.splitratio[1] < -2:
            self.splitratio[1] = -2


    def moveEndReshape(self, event):
        c = self.iconMaster
        num = event.num
        c.unbind("<B%d-Motion>"%num)
        c.unbind("<ButtonRelease-%d>"%num)


    def highlight(self, event=None):
        if self.iconMaster is None: return
        c = self.iconMaster
        apply( c.itemconfigure, (self.iconTag,), self.highlightOptions )

        
    def unhighlight(self, event=None):
        if self.iconMaster is None: return
        c = self.iconMaster
        apply( c.itemconfigure, (self.iconTag,), self.unhighlightOptions)
        

    def setColor(self, color):
        if self.iconMaster is None: return
        c = self.iconMaster
        apply( c.itemconfigure, (self.iconTag,), {'fill':color} )
        self.unhighlightOptions['fill'] = color
        self.deselectOptions['fill'] = color

        
    def getColor(self):
        return self.deselectOptions['fill']


    def select(self):
        self.selected = 1
        if self.iconMaster is None: return
        sum = self.port1.node.selected + self.port2.node.selected
        if sum==2:
            self.iconMaster.addtag('selected', 'withtag', self.iconTag)
        apply( self.iconMaster.itemconfigure, (self.iconTag,),
               self.selectOptions['connection%d'%sum] )


    def deselect(self):
        NetworkItems.deselect(self)
        if self.iconMaster is None: return
        sum = self.port1.node.selected + self.port2.node.selected
        if sum<2:
            self.iconMaster.dtag(self.iconTag, 'selected')
        if sum==0:
            opt = self.deselectOptions
        else:
            opt = self.selectOptions['connection%d'%sum]
        apply( self.iconMaster.itemconfigure, (self.iconTag,), opt )


    def shadowColors(self, colorTk):
        # for a given Tkcolor return a dark tone 40% and light tone 80%
        c = self.iconMaster
        maxi = float(c.winfo_rgb('white')[0])
        rgb = c.winfo_rgb(colorTk)
        base = ( rgb[0]/maxi*255, rgb[1]/maxi*255, rgb[2]/maxi*255 )
        dark = "#%02x%02x%02x"%(base[0]*0.6,base[1]*0.6,base[2]*0.6)
        light = "#%02x%02x%02x"%(base[0]*0.8,base[1]*0.8,base[2]*0.8)
        return dark, light


    def toggleBlocking_cb(self, event=None):
        self.blocking = not self.blocking
        self.isBlockingTk.set(self.blocking)
        if not self.blocking:
            self.port2.node.ensureRootNode()


    def toggleVisibility_cb(self, event=None):
        self.setVisibility(not self.hidden)


    def setVisibility(self, hidden):
        self.hidden = hidden
        del self.network.connById[self.id]
        if self.id2 is not None:
            del self.network.connById[self.id2]
        self.deleteIcon()
        self.buildIcons(self.network.canvas)
        self.network.connById[self.id] = self
        if self.id2 is not None:
            self.network.connById[self.id2] = self


    def reparent_cb(self, type):
        node = self.port2.node
        self.network.deleteConnections([self])
        node.reparentGeomType(type, reparentCurrent=False)
        

    def drawMapIcon(self, naviMap):
        if self.id is None: # geom nodes with aprentNode2 seen to create
            return          # conenctions with no id
        mapCanvas = naviMap.mapCanvas
        x0, y0 = naviMap.upperLeft
        scaleFactor = naviMap.scaleFactor
        canvas = self.iconMaster
        cc = self.network.canvas.coords(self.id)
        nc = []
        for i in range(0, len(cc), 2):
            nc.append( x0+cc[i]*scaleFactor )
            nc.append( y0+cc[i+1]*scaleFactor )

        if self.naviMapID is None:
            cid = mapCanvas.create_line( *nc, tag=('navimap',))
            self.naviMapID = cid
            return cid
        else:
            mapCanvas.coords(self.naviMapID, *nc)

        
    def updatePosition(self):
        
        if self.iconMaster is None:
            return
        
        # spoted by guillaume, I am not sure what it means
        if self.port1 is None or self.port2 is None:            
            import traceback
            traceback.print_stack()
            print c, id(id)
            print 'IT HAPPENED AGAIN: a conection is missing ports'
            return 

        if self.port1.id is None or self.port2.id is None:
            return # one the ports is not visible

        c = self.iconMaster

        coords = self.getLineCoords()
        if self.hidden is False:
            apply( c.coords, (self.id,)+tuple(coords) )
        else:
            if isinstance(self.port1, SpecialOutputPort):
                lcoords1 = (coords[0],coords[1],coords[0]+20,coords[1])
                lcoords2 = (coords[-2]-16,coords[-1],coords[-2],coords[-1])
            else:
                lcoords1 = (coords[0],coords[1],coords[0],coords[1]+20)
                lcoords2 = (coords[-2],coords[-1]-16,coords[-2],coords[-1])
            apply( c.coords, (self.id,)+tuple(lcoords1) )
            apply( c.coords, (self.id2,)+tuple(lcoords2) )

        naviMap = self.port1.node.network.naviMap
        self.drawMapIcon(naviMap)
        
        
    def getLineCoords(self):
        canvas = self.iconMaster
        c1 = self.port1.getCenterCoords()
        c2 = self.port2.getCenterCoords()
        n1 = self.port1.node
        n2 = self.port2.node
        if self._mode==1:
            if self.mode == 'straight':
                outOffy = c1[1]+15
                inOffy = c2[1]-15
                return [ c1[0], c1[1], c1[0], outOffy,
                         c2[0], inOffy, c2[0], c2[1] ]

            else: # if self.mode == 'angles':
                dy = c2[1]-c1[1]
                if dy > 30:     # draw just 1 segment down, 1 horizontal and 1 down again
                    dy2 = dy * self.splitratio[1]
                    outOffy = c1[1]+dy2
                    return [ c1[0], c1[1], c1[0], outOffy, c2[0],
                             outOffy, c2[0], c2[1] ]
                else:
                    outOffy = c1[1]+15  # go down 15 pixels from output
                    inOffy = c2[1]-15   # go up 15 pixel from input
                    dx = c2[0]-c1[0]
                    dx2 = dx * self.splitratio[0]
                    mid = [ c1[0]+dx2, outOffy, c2[0]-(dx-dx2), inOffy ]
                    return [ c1[0], c1[1], c1[0], outOffy ] + mid + \
                           [ c2[0], inOffy, c2[0], c2[1] ]
        else:
            vx1, vy1 = self.port1.vectorRotated
            vy1 = -vy1
            vx2, vy2 = self.port2.vectorRotated
            vy2 = -vy2
            if self.mode == 'straight':
                outOffy = c1[0]+15*vx1
                inOffy = c2[0]-15*vy1
                return [ c1[0], c1[1], c1[0], outOffy,
                         c2[0], inOffy, c2[0], c2[1] ]

            else: # if self.mode == 'angles':
                dx = c2[0]-c1[0]
                # check if port vectors are opposite
                dot =  vx1*vx2 + vy1*vy2
                if dot < 0.0: # 3 segments, 2 projecting out of node and 1 joining them
                    # draw 1 segment along p1.vector
                    # 1 segment along -p2.vector and a segement joing them
                    proj = 20
                    p1x = c1[0]+proj*vx1
                    p1y = c1[1]+proj*vy1
                    p2x = c2[0]+proj*vx2
                    p2y = c2[1]+proj*vy2
                    #print 'getLineCoords A',c1[0], c1[1], p1x, p1y, p2x, p2y, c2[0], c2[1]
                    #print 'A', c1, c2, vx1, vy1, vx2, vy2
                    return [ c1[0], c1[1], p1x, p1y, p2x, p2y, c2[0], c2[1] ]
                else:
                    proj = 20
                    p1x = c1[0]+proj*vx1 # move up
                    p1y = c1[1]+proj*vy1
                    perp = -vy1, vx1
                    # check that perpendicular vector point from on port to the other
                    ppvx = c2[0]-c1[0] # vector form port1 to port2
                    ppvy = c2[1]-c1[1]
                    dot = ppvx*perp[0] + ppvy*perp[1]
                    if dot>0.0: sign = 1.0
                    else: sign = -1.0
                    p2x = p1x+proj*sign*perp[0] # move side ways a bit
                    p2y = p1y+proj*sign*perp[1]
                    p3x = c2[0]+proj*vx2
                    p3y = c2[1]+proj*vy2
                    #print 'B', c1, c2, vx1, vy1, vx2, vy2, perp
                    #print 'getLineCoords B',  c1[0], c1[1], p1x, p1y, p2x, p2y, p3x, p3y,c2[0], c2[1]
                    return [ c1[0], c1[1], p1x, p1y, p2x, p2y, p3x, p3y,
                             c2[0], c2[1] ]

##      def getLineCoords(self):
##         if isinstance(self.port1, SpecialOutputPort):
##             return self.getLineCoordsLeftRightPorts()
##         elif isinstance(self.port1, ImageOutputPort):
##             return self.getLineCoordsLeftRightPorts()
##         else:
##             return self.getLineCoordsTopBottomPorts()

        
##     def getLineCoordsLeftRightPorts(self):
##         canvas = self.iconMaster
##         c1 = self.port1.getCenterCoords()
##         c2 = self.port2.getCenterCoords()
##         if self.mode == 'straight':
##             outOffy = c1[0]+15
##             inOffy = c2[0]-15
##             return [ c1[0], c1[1], c1[0], outOffy,
##                      c2[0], inOffy, c2[0], c2[1] ]

##         else: # if self.mode == 'angles':
##             dx = c2[0]-c1[0]
##             if dx > 30:     # draw just 1 segment down, 1 horizontal and 1 down again
##                 dx2 = dx * self.splitratio[0]
##                 outOffx = c1[0]+dx2
##                 inOffx = c2[0]-(dx-dx2)
##                 return [ c1[0], c1[1], outOffx, c1[1], inOffx, c2[1],
##                          c2[0], c2[1] ]
##             else:
##                 outOffx = c1[0]+15  # go right 15 pixels from output
##                 inOffx = c2[0]-15   # go left 15 pixel from input
##                 dy = c2[1]-c1[1]
##                 dy2 = dy * self.splitratio[1]
##                 mid = [ outOffx, c1[1]+dy2, inOffx, c2[1]-(dy-dy2) ]
##                 return [ c1[0], c1[1], outOffx, c1[1] ] + mid + \
##                        [ inOffx, c2[1], c2[0], c2[1] ]
 


##     def getLineCoordsTopBottomPorts(self):
##         # implements straight and angle connections between nodes
##         canvas = self.iconMaster
##         c1 = self.port1.getCenterCoords()
##         c2 = self.port2.getCenterCoords()
##         if self.mode == 'straight':
##             outOffy = c1[1]+15
##             inOffy = c2[1]-15
##             return [ c1[0], c1[1], c1[0], outOffy,
##                      c2[0], inOffy, c2[0], c2[1] ]

##         else: # if self.mode == 'angles':
##             dy = c2[1]-c1[1]
##             if dy > 30:     # draw just 1 segment down, 1 horizontal and 1 down again
##                 dy2 = dy * self.splitratio[1]
##                 outOffy = c1[1]+dy2
##                 return [ c1[0], c1[1], c1[0], outOffy, c2[0],
##                          outOffy, c2[0], c2[1] ]
##             else:
##                 outOffy = c1[1]+15  # go down 15 pixels from output
##                 inOffy = c2[1]-15   # go up 15 pixel from input
##                 dx = c2[0]-c1[0]
##                 dx2 = dx * self.splitratio[0]
##                 mid = [ c1[0]+dx2, outOffy, c2[0]-(dx-dx2), inOffy ]
##                 return [ c1[0], c1[1], c1[0], outOffy ] + mid + \
##                        [ c2[0], inOffy, c2[0], c2[1] ]


    def buildIcons(self, canvas):
        """Build CONNECTION icon
"""
        NetworkItems.buildIcons(self, canvas)

        kw = self.lineOptions
        arcTag = '__arc'+str(self.arcNum)
        self.arcNum = self.arcNum + 1
        kw['tags'] = ('connection', arcTag)
        coords = self.getLineCoords()
        if self.hidden is False:
            g = apply( canvas.create_line, tuple(coords), kw )
        else:
            #print "coords", coords
            if isinstance(self.port1, SpecialOutputPort):
                lcoords1 = (coords[0],coords[1],coords[0]+20,coords[1])
                lcoords2 = (coords[-2]-16,coords[-1],coords[-2],coords[-1])
            else:
                lcoords1 = (coords[0],coords[1],coords[0],coords[1]+20)
                lcoords2 = (coords[-2],coords[-1]-16,coords[-2],coords[-1])
            g = apply( canvas.create_line, tuple(lcoords1), kw )
            g2 = apply( canvas.create_line, tuple(lcoords2), kw )
            self.iconTag2 = 'conn'+str(g2)
            self.id2 = g2

        self.iconTag = 'conn'+str(g)
        self.id = g

        cb = CallBackFunction(self.network.deleteConnections, ([self]))
        
        if self.port2.name == 'parent' and hasattr(self.port2.node,'selectedGeomIndex'): 
            # i.e. it's a geometry node          
            cbSiblings = CallBackFunction(self.reparent_cb, ('siblings'))
            cbAll = CallBackFunction(self.reparent_cb, ('all'))
            self.menu.add_command(label='delete / reparent to root', command=cb)
            self.menu.add_command(label='reparent pointed siblings to root', command=cbSiblings)
            self.menu.add_command(label='reparent all pointed geoms to root', command=cbAll)
        else: 
            self.menu.add_command(label='delete', command=cb)

        if self.hidden is False:
            self.menu.add_command(label='hide', command=self.toggleVisibility_cb)
        else:
            self.menu.add_command(label='show', command=self.toggleVisibility_cb)
        self.menu.add_checkbutton(label='blocking',
                                  variable = self.isBlockingTk,
                                  command=self.toggleBlocking_cb)

        # adding the self.id as a unique tag for this node
        canvas.addtag_withtag(self.iconTag, arcTag )
        if self.hidden is True:
            canvas.addtag_withtag(self.iconTag2, arcTag )

        canvas.dtag( arcTag )
        canvas.lower(g, 'node')


    def getSourceCode(self, networkName, selectedOnly=0, indent="", ignoreOriginal=False, connName='conn'):
        # build and return connection creation source code

        from NetworkEditor.ports import TriggerOutputPort

        lines = []
        conn = self

        if conn._original is True and ignoreOriginal is False:
            return lines

        if selectedOnly and \
           conn.port1.node.selected+conn.port2.node.selected < 2:
            return lines

        node1 = conn.port1.node
        node2 = conn.port2.node

        n1Name = node1.getUniqueNodeName()
        n2Name = node2.getUniqueNodeName()

        lines = node1.checkIfNodeForSavingIsDefined(lines, networkName, indent)
        lines = node2.checkIfNodeForSavingIsDefined(lines, networkName, indent)

        lines.append(indent+'if %s is not None and %s is not None:\n'%(
            n1Name, n2Name))
        if isinstance(conn.port1, TriggerOutputPort):
            line1 = networkName+".specialConnectNodes(\n"
        else:
            line1 = '%s = '%connName +networkName+".connectNodes(\n"
##         line = line + "%s, %s, %d, %d)\n"%(n1Name, n2Name,
##                                           conn.port1.number, conn.port2.number)

        port1Name = conn.port1.name
        port2Name = conn.port2.name

        from macros import MacroInputNode, MacroOutputNode
        # treat connections to MacroInputNode separately
        if isinstance(conn.port1.node, MacroInputNode):
            if len(conn.port1.connections) > 1:
                i = 0
                for c in conn.port1.connections:
                    if c == conn:
                        break
                    else:
                        i = i + 1
                if i == 0:
                    port1Name = 'new'
            else:
                port1Name = 'new'

        # treat connections to MacroOutpuNode separately
        if isinstance(conn.port2.node, MacroOutputNode):
            if len(conn.port2.connections) > 1:
                i = 0
                for c in conn.port2.connections:
                    if c == conn:
                        break
                    else:
                        i = i + 1
                if i == 0:
                    port2Name = 'new'
            else:
                port2Name = 'new'

        line2 = '%s, %s, "%s", "%s", blocking=%s\n'%(
            n1Name, n2Name, port1Name, port2Name, conn.blocking)

        line3 = ''
        if conn.splitratio != [.5,.5]:
            line3 = ', splitratio=%s'%(conn.splitratio)
        if self.hidden is True:
            line3 += ', hidden=True'
        line3 += ')\n'

        lines.append(indent + ' '*4 + 'try:\n')
        lines.append(indent + ' '*8 + line1)
        lines.append(indent + ' '*12 + line2)
        lines.append(indent + ' '*12 + line3)
        lines.append(indent + ' '*4 + 'except:\n')
        lines.append(indent + ' '*8 + \
            'print "WARNING: failed to restore connection between %s and %s in network %s"\n'%(n1Name,n2Name,networkName))

        lines.extend(node1.customizeConnectionCode(self, connName, indent + ' '*4))
        lines.extend(node2.customizeConnectionCode(self, connName, indent + ' '*4))
        return lines


    def destroyIcon(self):
        self.deleteIcon()
        self.id = None
        self.iconMaster = None
        
        self.id2 = None
        self.network.canvas.delete(self.iconTag2)
        self.iconTag2 = None
        self.naviMapID = None
        


class FunctionNode(NetworkNode):
    """
    Base node for Vsiion nodes exposing a function or callable object
    
    The RunFunction node is an example of subclassing this node.
    Opal web services nodes are instance of this node exposing the
    opal web service python wrapper callable object

    This object support creating input ports for all parameters to the
    function. Positional (i.e. without default value) arguments always
    generate an input port visible on the node. For named arguments arguments
    a widget is created base on the type of the default value (e.g. entry for
    string, dial for int and float etc.)
    
    If the function or callable object has a .params attribute this attribute is
    expected to be a dictionary where the key is the name of the argument and the\
    value is dictionary providing additional info about this parameter.
    the folloing keys are recognized in this dictionary:
        {'default': 'False', # default value (not used as it is taken from the function signature)
         'type': 'boolean', 
         'description': 'string' #use to create tooltip
         'ioType': 'INPUT', # can be INPUT, INOUT, 
        }
        if type is FILE a a file browser will be generated
        if type is selection a values keywords should be present and provide a list
        of possible values that will be made available in a combobox widget
    """

    codeBeforeDisconnect = """def beforeDisconnect(self, c):
    # upon disconnecting we want to set the attribute function to None
    c.port2.node.function = None
    # remove all ports beyond the 'function' and 'importString' input ports
    for p in c.port2.node.inputPorts[2:]:
        c.port2.node.deletePort(p)
"""

    def passFunction():
        pass
    passFunc = passFunction


    def __init__(self, functionOrString=None, importString=None,
                 posArgsNames=[], namedArgs={}, **kw):

        if functionOrString is not None or kw.has_key('functionOrString') is False:
            kw['functionOrString'] = functionOrString
        elif kw.has_key('functionOrString') is True:
            functionOrString = kw['functionOrString']
        if importString is not None or kw.has_key('importString') is False:
            kw['importString'] = importString
        elif kw.has_key('importString') is True:
            importString = kw['importString']
        if len(posArgsNames)>0 or kw.has_key('posArgsNames') is False:
            kw['posArgsNames'] = posArgsNames
        elif kw.has_key('posArgsNames') is True:
            posArgsNames = kw['posArgsNames']
        if len(namedArgs)>0 or kw.has_key('namedArgs') is False:
            kw['namedArgs'] = namedArgs
        elif kw.has_key('namedArgs') is True:
            namedArgs = kw['namedArgs']

        if type(functionOrString) == types.StringType:
            # we add __main__ to the scope of the local function
            # the folowing code is similar to: "from __main__ import *"
            # but it doesn't raise any warning, and its probably more local
            # and self and in1 are still known in the scope of the eval function
            from mglutil.util.misc import importMainOrIPythonMain
            lMainDict = importMainOrIPythonMain()
            for modItemName in set(lMainDict).difference(dir()):
                locals()[modItemName] = lMainDict[modItemName]

            if importString is not None:
                try:
                    lImport = eval(importString)
                    if lImport == types.StringType:
                        importString = lImport
                except:
                    pass
                exec(importString)
            if kw.has_key('masternet') is True:
                masterNet = kw['masternet']
            lfunctionOrString = functionOrString
            while type(lfunctionOrString) == types.StringType:
                try:
                    function = eval(lfunctionOrString)
                except NameError:
                    function = None
                lfunctionOrString = function
        else:
            function = functionOrString

        if function is not None and kw.has_key('library'):
            # so we know where to find the current editor
            function._vpe = kw['library'].ed
            function._node = self # so we can find the vision node

        if hasattr(function, 'params') and type(function.params) == types.DictType:
            argsDescription = function.params
        else:
            argsDescription = {}

        if inspect.isclass(function) is True:
            try:
                function = function()
            except:
                function = None 

        if function is None:
            #def testFunction(a, b=1):
            #    print 'testFunction', a, b
            #    return a, b
            function = self.passFunc

        if hasattr(function, 'name'):
            name = function.name
        elif hasattr(function, '__name__'):
            name = function.__name__
        else:
            name = function.__class__.__name__

        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.function = function # function or command to be called
        
        self.posArgsNames = posArgsNames
        self.namedArgs = namedArgs # dict:  key: arg name, value: arg default

        self.outputPortsDescr.append(datatype='None', name='result')
        #for key, value in outputDescr:
        #    self.outputPortsDescr.append(datatype=value, name=key)

        # get arguments description
        from inspect import getargspec
        if hasattr(function, '__call__') and hasattr(function.__call__, 'im_func'): 
            args = getargspec(function.__call__.im_func)
        else:
            args = getargspec(function)

        if len(args[0])>0 and args[0][0] == 'self':
            args[0].pop(0) # get rid of self

        allNames = args[0]

        defaultValues = args[3]
        if defaultValues is None:
            defaultValues = []
        nbNamesArgs = len(defaultValues)
        if nbNamesArgs > 0:
            self.posArgsNames = args[0][:-nbNamesArgs]
        else:
            self.posArgsNames = args[0]
        d = {}
        for name, val in zip(args[0][-nbNamesArgs:], defaultValues):
            d[name] = val

        self.namedArgs = d

        # create widgets and ports for named arguments
        self.buildPortsForPositionalAndNamedArgs(self.posArgsNames,
                                                 self.namedArgs,
                                                 argsDescription=argsDescription)

        # create the constructor arguments such that when the node is restored
        # from file it will have all the info it needs
        if functionOrString is not None \
          and type(functionOrString) == types.StringType:
            self.constrkw['functionOrString'] = "\'"+suppressMultipleQuotes(functionOrString)+"\'"
            if importString is not None:
                self.constrkw['importString'] = "\'"+suppressMultipleQuotes(importString)+"\'"
        elif hasattr(function, 'name'):
            # case of a Pmv command
            self.constrkw['command'] = 'masterNet.editor.vf.%s'%function.name
        elif hasattr(function, '__name__'):
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = "\'"+function.__name__+"\'"
        else:
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = "\'"+function.__class__.__name__+"\'"
        if (importString is None or importString == '') \
          and self.constrkw.has_key('importString') is True:
            del self.constrkw['importString']
        if len(self.posArgsNames) > 0:
            self.constrkw['posArgsNames'] = self.posArgsNames
        elif self.constrkw.has_key('posArgsNames') is True:
            del self.constrkw['posArgsNames']
        if len(self.namedArgs) > 0:
            self.constrkw['namedArgs'] = self.namedArgs
        elif self.constrkw.has_key('namedArgs') is True:
            del self.constrkw['namedArgs']
        if kw.has_key('host') is True:
            self.constrkw['host'] = '\"'+suppressMultipleQuotes(kw['host'])+'\"'
        elif self.constrkw.has_key('host') is True:
            del self.constrkw['host']

        code = """def doit(self, *args):
    # get all positional arguments
    posargs = []
    for pn in self.posArgsNames:
        posargs.append(locals()[pn])
    # build named arguments
    kw = {}
    for arg in self.namedArgs.keys():
        kw[arg] = locals()[arg]
    # call function
    try:
        if hasattr(self.function,'__call__') and hasattr(self.function.__call__, 'im_func'):
            result = apply( self.function.__call__, posargs, kw )
        else:
            result = apply( self.function, posargs, kw )
    except Exception, e:
        from warnings import warn
        warn(str(e))
        result = None
    self.outputData(result=result)
"""
        if code: self.setFunction(code)
        # change signature of compute function
        self.updateCode(port='ip', action='create', tagModified=False)


    def buildPortsForPositionalAndNamedArgs(self, args, namedArgs, argsDescription={},
                                            createPortNow=False):

        lAllPortNames = args + namedArgs.keys()
        for name in lAllPortNames:
            if name in args:
                ipdescr = {'name':name, 'required':True}
                if argsDescription.get(name):
                    lHasDefaultValue = True
                    val = argsDescription[name]['default']
                else:
                    lHasDefaultValue = False
            else:
                ipdescr = {'name':name, 'required':False}
                lHasDefaultValue = True
                val = namedArgs[name]

            dtype = 'None'
            if lHasDefaultValue is True:
                if argsDescription.get(name) and argsDescription[name]['type']=='selection':
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEComboBox',
                        'initialValue':val,
                        'choices':argsDescription[name]['values'],
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif argsDescription.get(name) \
                  and argsDescription[name]['type']=='FILE' \
                  and (   argsDescription[name]['ioType']=='INPUT' \
                       or argsDescription[name]['ioType']=='INOUT'):
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEEntryWithFileBrowser',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) is types.BooleanType:
                    dtype = 'boolean'
                    self.widgetDescr[name] = {
                        'class': 'NECheckButton',
                        'initialValue':val==True,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) in [ types.IntType, types.LongType]:
                    dtype = 'int'
                    self.widgetDescr[name] = {
                        'class': 'NEDial', 'size':50,
                        'showLabel':1, 'oneTurn':1, 'type':'int',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) in [types.FloatType, types.FloatType]:
                    dtype = 'float'
                    self.widgetDescr[name] = {
                        'class': 'NEDial', 'size':50,
                        'showLabel':1, 'oneTurn':1, 'type':'float',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) is types.StringType:
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEEntry', 'width':10,
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
    
                if argsDescription.get(name):
                    self.widgetDescr[name]['labelBalloon'] = argsDescription[name]['description']

                ipdescr.update({'datatype':dtype,
                        'balloon':'Defaults to '+str(val),
                        'singleConnection':True})

            self.inputPortsDescr.append( ipdescr )

            if createPortNow is True:
                # create port
                ip = apply( self.addInputPort, (), ipdescr )
                # create widget if necessary
                if dtype != 'None':
                    ip.createWidget(descr=self.widgetDescr[name])


def inSegment( p, s1, s2):
## inSegment(): determine if a point is inside a segment
##     Input:  a point p, and a collinear segment [s1,s2]
##     Return: 1 = P is inside S
##             0 = P is not inside S
    if s1[0] != s2[0]:    # [s1,s2] is not vertical
        if s1[0]<=p[0] and p[0]<=s2[0]:
            return True
        if s1[0]>=p[0] and p[0]>=s2[0]:
            return True
    else: # S is vertical, so test y coordinate
        if s1[1]<=p[1] and p[1]<=s2[1]:
            return True
        if s1[1]>=p[1] and p[1]>=s2[1]:
            return True
    return False

def perp( a ):
    # return 2D vector orthogonal to a
    b = [0,0]
    b[0] = -a[1]
    b[1] = a[0]
    return b

def seg_intersect(a1, a2, b1, b2) :
# line segment a given by endpoints a1, a2
# line segment b given by endpoints b1, b2
# return x,y of intersection of 2 segments or None, None
    da = (a2[0]-a1[0], a2[1]-a1[1])
    db = (b2[0]-b1[0], b2[1]-b1[1])
    dp = (a1[0]-b1[0], a1[1]-b1[1])
    dap = perp(da)
    denom = numpy.dot( dap, db)
    if denom==0.0:
        return None, None
    num = numpy.dot( dap, dp )
    l = (num / denom)
    return l*db[0]+b1[0], l*db[1]+b1[1]


##
## Image nodes are node for which the node is represented by an image rendered
## using pycairo and added to the canvas rather than using Tkinter.Canvas
## primitives
##
def rotateCoords(center, coords, angle):
    """
    Rotate a list of 2D coords around the center by an angle given in degrees
    """
    cangle = cmath.exp(angle*1j*math.pi/180)
    offset = complex(center[0], center[1])
    rotatedxy = []
    for i in range(0, len(coords), 2):
        v = cangle * (complex(coords[i], coords[i+1]) - offset) + offset
        rotatedxy.append(v.real)
        rotatedxy.append(v.imag)
    return rotatedxy

class NodeStyle:
    """
    Class to define the rendering style of a node.

    Every node has a NodeStyle instance that is used to render the node's image.
    The VPE has a NodeStylesManager that stores alternate styles for each node
    
    """
    def __init__(self, **kw): #flowDirection='leftRight'
        self.rotAngle = 0.0
        self.width = None
        self.height = None
        self.fillColor = [0.82, 0.88, 0.95, 0.5]
        self.outlineColor = [0.28, 0.45, 0.6, 1.]

        self.inputPorts = {}
        self.iportNumToName = [] # list of names of input ports 
        self.outputPorts = {}
        self.oportNumToName = [] # list of names of output ports 
        
        self.configure(**kw)
        
        #if flowDirection=='leftRight':
        #    sideIn = 'left'
        #    sideOut = 'right'
        #elif flowDirection=='topBottom':
        #    sideIn = 'top'
        #    sideOut = 'bottom'
        #else:
        #    raise RuntimeError, "bad flowDirection"
        #self.flowDirection = flowDirection

    def getPortXY(self, descr, node):
        ulx, uly = node.UL
        width = node.activeWidth
        height = node.activeHeight

        dx, dy = descr.get('ulrpos', (None, None))
        if dx is not None:
            if abs(dx) < 1.0: dx *= width
            if abs(dy) < 1.0: dy *= height
            return ulx+dx, uly+dy

        dx, dy = descr.get('urrpos', (None, None))
        if dx is not None:
            if abs(dx) < 1.0: dx *= width
            if abs(dy) < 1.0: dy *= height
            return ulx+width+dx, uly+dy

        dx, dy = descr.get('llrpos', (None, None))
        if dx is not None:
            if abs(dx) < 1.0: dx *= width
            if abs(dy) < 1.0: dy *= height
            return ulx+dx, uly+height+dy

        dx, dy = descr.get('lrrpos',(None, None))
        if dx is not None:
            if abs(dx) < 1.0: dx *= width
            if abs(dy) < 1.0: dy *= height
            return ulx+width+dx, uly+height+dy

        # fixme .. find a good location for this port
        return ulx+10, uly

        
    def getEdge(self, styleDict):
        for k,v in styleDict.items():
            if k[-4:]=='rpos':
                found = True
                break
        if not found:
            print 'PORT EDGE NOT FOUND %rpos key missing using "top"', portNum, descr
            return 'top'
        if k=='ulrpos':
            if v[0]==0: return 'left'
            else: return 'top'
        elif k=='urrpos':
            if v[0]==0: return 'right'
            else: return 'top'
        elif k=='llrpos':
            if v[0]==0: return 'left'
            else: return 'bottom'
        elif k=='lrrpos':
            if v[0]==0: return 'right'
            else: return 'bottom'


    def setInputPortStyles(self, ipStyles):
        for name, styleDict in ipStyles:
            self.iportNumToName.append(name)
            styleDict['edge'] = self.getEdge(styleDict)
            self.inputPorts[name] =  styleDict

            
    def setOutputPortStyles(self, opStyles):
        for name, styleDict in opStyles:
            self.oportNumToName.append(name)
            styleDict['edge'] = self.getEdge(styleDict)
            self.outputPorts[name] =  styleDict
        
    
    def configure(self, **kw):
        width = kw.get('width', None)
        if width:
            if width > 0 and isinstance(width, (int, float)):
                self.width = width
            else:
                print 'WARNING bad width', width, type(width)
            
        height = kw.get('height', None)
        if height:
            if height > 0 and isinstance(height, (int, float)):
                self.height = height
            else:
                print 'WARNING bad height', height, type(height)
            
        rotAngle = kw.get('rotAngle', None)
        if rotAngle is not None:
            if isinstance(rotAngle, (int, float)):
                self.rotAngle = rotAngle
            else:
                print 'WARNING bad rotAngle', rotAngle, type(rotAngle)
            
        fillColor = kw.get('fillColor', None)
        if fillColor:
            if len(fillColor)==3 and isinstance(fillColor[0], float):
                self.fillColor[:3] = fillColor
            elif len(fillColor)==4 and isinstance(fillColor[0], float):
                self.fillColor = fillColor[:]
            else:
                print 'WARNING bad fillColor', fillColor, type(fillColor)

        outlineColor = kw.get('outlineColor', None)
        if outlineColor:
            if len(outlineColor)==3 and isinstance(outlineColor[0], float):
                self.outlineColor[:3] = outlineColor
            elif len(outlineColor)==4 and isinstance(outlineColor[0], float):
                self.outlineColor = outlineColor[:]
            else:
                print 'WARNING bad outlineColor', outlineColor, type(outlineColor)

        inputPorts = kw.get('inputPorts', None)
        if inputPorts:
            assert isinstance(inputPorts, dict)
            self.inputPorts = inputPorts.copy()

        outputPorts = kw.get('outputPorts', None)
        if outputPorts:
            assert isinstance(outputPorts, dict)
            self.outputPorts = outputPorts.copy()

        iportNumToName = kw.get('iportNumToName', None)
        if iportNumToName:
            assert isinstance(iportNumToName, list)
            self.iportNumToName = iportNumToName[:]

        oportNumToName = kw.get('oportNumToName', None)
        if oportNumToName:
            assert isinstance(oportNumToName, list)
            self.oportNumToName = oportNumToName[:]

        
    def getStyle(self):
        style = {'width':self.width,
                 'height':self.height,
                 'fillColor': self.fillColor,
                 'outlineColor': self.outlineColor,
                 'rotAngle': self.rotAngle,
                 'inputPorts': self.inputPorts,
                 'iportNumToName' : self.iportNumToName,
                 'outputPorts': self.outputPorts,
                 'oportNumToName' : self.oportNumToName,
             }
        return style


    def copy(self):
        return self.__class__(
            width = self.width,
            height = self.height,
            rotAngle = self.rotAngle, 
            fillColor = self.fillColor[:],
            outlineColor = self.outlineColor[:],
            inputPorts = self.inputPorts.copy(),
            iportNumToName = self.iportNumToName[:],
            outputPorts = self.outputPorts.copy(),
            oportNumToName = self.oportNumToName[:]
            )

    
    def getSize(self): return self.width, self.height
    def getFillColor(self): return self.fillColor
    def getOutlineColor(self): return self.outlineColor
    def getAngle(self): return self.rotAngle

    
class ImageNode(NetworkNode):


    #def edit(self, event=None):
        #if self.objEditor:
        #    self.objEditor.top.master.lift()
        #    return

        #from ImageNodeEditor import ImageNodeEditor
        #self.objEditor = ImageNodeEditor(self)
        

    def saveStylesDefinition(self):
        # now save style in styles folder
        from mglutil.util.packageFilePath import getResourceFolderWithVersion
        sm = self.editor.nodeStylesManager
        styles = sm.getStylesForNode(self)
        visionrcDir = getResourceFolderWithVersion()
        folder = os.path.join(visionrcDir, 'Vision', 'nodeStyles')
        filename = os.path.join(folder, "%s__%s.py"%(
            self.library.name.replace('.', '___'), self.__class__.__name__))
        f = open(filename, 'w')
        f.write("styles = {\n")
        default = styles.get('default', styles.keys()[0])
        f.write("    'default' : '%s',\n"%default)
        for name, style in styles.items():
            if name=='default': continue
            f.write("    '%s' : %s,\n"%(name, str(style.getStyle())))
        f.write("  }\n")
        f.close()

        
    ## def getStylesDefinitionSourceCode(self, indent):
    ##     #'EwSignals_v0.1|EwAmpDelaySignal' : {
    ##     #    'default' : 'square80'
    ##     #    'square80' :        {'width':80, 'height':80},
    ##     #    'small rectangle' : {'width':200, 'height':120},
    ##     #    'large rectangle' : {'width':300, 'height':240},
    ##     #    },
    ##     lines = []
    ##     lines.append(indent+"'%s|%s' : {\n"%(self.library.name, self.__class__.__name__))
    ##     indent1 = indent + '    '
    ##     for name, style in self.styles.items():
    ##         lines.append(indent1+"'%s' : %s,\n"%(name, str(style)))
    ##     lines.append(indent+"},\n")
        
    ##     return lines


    def __init__(self, name='NoName', library=None, iconFileName=None,
                 iconPath='', **kw):
        """
        This class implements a NetworkNode that is rendered using a single
        image generated using pycairo
        """
        
        constrkw = kw.pop('constrkw', None)
        NetworkNode.__init__(*(self, name, None, constrkw, None, library, 0), **kw)
        # posx and posy are upper left corner of BoundingBox(self.innerBox)
        self.center= [0,0] # coords of node's center in canvas
        self.rotAngle = 0.0 # keep track of rotation angle
        self.selectOptions = {}
        self.deselectOptions = {}
        self.iconPath = iconPath
        self.iconFileName = iconFileName
        
        # create the node renderer
        from NetworkEditor.drawNode import CairoNodeRenderer
        self.renderer = CairoNodeRenderer()

        self.posx = None # x coord of upper left corner of the node's image
        self.posy = None # y coord of upper left corner of the node's image
        self.activeWidth = None # length of not node's box
        self.activeheight = None # height of not node's box
        self.UL = (None, None) # offset of upper left corner of box in image

        # node styles
        self.nodeStyle = None
        self.currentNodeStyle = None # None means no predefined style is applied
                                     # else it is the name of the style

        
    def resize(self, event):
        self.startDrawingResizeBox(event)


    def startDrawingResizeBox(self, event):
        num = event.num
        self.mouseButtonFlag = self.mouseButtonFlag & ~num

        canvas = self.network.canvas
        canvas.configure(cursor="bottom_right_corner")
        x1, y1, x2, y2 = self.getBoxCorners()
	self.origx = x1
	self.origy = y1
	x = canvas.canvasx(event.x)
	y = canvas.canvasy(event.y)
        self.hasMoved = 0
        canvas.bind("<ButtonRelease-%d>"%num, self.endResizeBox)
        canvas.bind("<B%d-Motion>"%num, self.resizeBox)
        self.resizeBoxID = canvas.create_rectangle(x1, y1, x2, y2, outline='green')
  
    # function to draw the box
    def selectionBoxMotion(self, event):
        self.ResizeBox(event)
        

    # call back for motion events
    def resizeBox(self, event):
        canvas = self.network.canvas
        #if self.resizeBoIDx: canvas.delete(self.resizeBoxID)
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        # check if the mouse moved only a few pixels. If we are below a
        # threshold we assume we did not move. This is usefull for deselecting
        # nodes for people who don't have a steady hand (who move the mouse
        # when releasing the mouse button, or when the mouse pad is very soft
        # and the  mouse moves because it is pressed in the pad...)
        if abs(self.origx-x) < 10 or abs(self.origy-y) < 10:
            self.hasMoved = 0
        else:
            self.hasMoved = 1
            canvas.coords(self.resizeBoxID, self.origx, self.origy, x, y)
            x1, y1, x2, y2 = canvas.bbox(self.resizeBoxID)
            self.nodeStyle.configure(width=x2-x1, height=y2-y1)
            self.boxCorners = self.getBoxCorners()
            self.redrawNode()
            #print 'ORIG2', self.origx, self.origy, x, y, canvas.bbox(self.resizeBoxID)
    

    # callback for ending command
    def endResizeBox(self, event):
        canvas = self.network.canvas
        canvas.configure(cursor="")
        
        x1, y1, x2, y2 = canvas.bbox(self.resizeBoxID)
        width = self.activeWidth = x2-x1
        height = self.activeHeight = y2-y1
        self.nodeStyle.configure(width=width, height=y2-y1)
        self.redrawNode()

        canvas.delete(self.resizeBoxID)
        num = event.num
        self.mouseButtonFlag = self.mouseButtonFlag & ~num
  	canvas.unbind("<B%d-Motion>"%num)
	canvas.unbind("<ButtonRelease-%d>"%num)
        del self.origx
        del self.origy
        del self.resizeBoxID
        
        self.currentNodeStyle = None # set the a style name that is a key in
              # ed.nodeStylesManager.styles OR set to None when  the style is modified
              # but not saved as a style
                                              

    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):

        self.nameInSavedFile = self.getUniqueNodeName()

        # specialize this method to save the the system configuration
        lines = NetworkNode.getNodeDefinitionSourceCode(
            self, networkName, indent=indent, ignoreOriginal=ignoreOriginal)

        # save node rotation
        if self.rotAngle !=0.0:
            lines.append( indent + '%s.rotate(%f)\n'%(
                self.nameInSavedFile, self.rotAngle))

        from NetworkEditor.macros import MacroNetwork
        if isinstance(self.network, MacroNetwork):
            if hasattr(self.network.macroNode, 'nameInSavedFile') and \
                   self.network.macroNode.nameInSavedFile: # we are saving the macro
                name = "%s.macroNetwork.nodes[%d]"%(
                    self.network.macroNode.nameInSavedFile, # <- this break copy of network in macro
                    self.network.nodeIdToNumber(self._id))
            else: # we are copying the network in  a macro
                name = self.nameInSavedFile
        else:
            name = self.nameInSavedFile

        if self.currentNodeStyle: # we have a predefined style
            lines.append( indent + '%s.setStyle("%s")\n'%(
                name, self.currentNodeStyle))
        else: # the style is modified but not saved as a template
            lines.append( indent + 'nodeStyle = %s\n'%self.nodeStyle.getStyle())
            lines.append( indent + '%s.nodeStyle.configure(**nodeStyle)\n'%(
                name))
            
        return lines


    def autoResizeX(self):
        return


    def drawMapIcon(self, naviMap):
        canvas = naviMap.mapCanvas
        x0, y0 = naviMap.upperLeft
        scaleFactor = naviMap.scaleFactor
        c = self.getBoxCorners()
        cid = canvas.create_rectangle(
            [x0+c[0]*scaleFactor, y0+c[1]*scaleFactor,
             x0+c[2]*scaleFactor, y0+c[3]*scaleFactor],
            fill='grey50', outline='black', tag=('navimap',))
        ## import Image
        ## im = self.imShadow1
        ## self.scaledImage = im.resize((int(im.size[0]*scaleFactor),
        ##                               int(im.size[1]*scaleFactor)), Image.ANTIALIAS)
        ## self.mapImagetk = ImageTk.PhotoImage(image=self.scaledImage)
        ## cid = canvas.create_image( x0+self.posx*scaleFactor, y0+self.posy*scaleFactor,
        ##                            image=self.mapImagetk)
        self.naviMapID = cid
        return cid


    def deleteIcon(self):
        NetworkNode.deleteIcon(self)
        if hasattr(self, 'imagetk'):
            del self.imagetk # else the selected rendered node remains
        if hasattr(self, 'imagetkRot'):
            del self.imagetkRot # else the selected rendered node remains
        if hasattr(self, 'imagetkSel'):
            del self.imagetkSel # else the selected rendered node remains
        if hasattr(self, 'imagetkSelRot'):
            del self.imagetkSelRot # else the selected rendered node remains


    def select(self):
        canvas = self.iconMaster
        tags = canvas.itemcget(self.id, 'tags').split()
        NetworkNode.select(self)
        canvas.itemconfigure(self.innerBox, tags=tags+['selected'],
                             image = self.imagetkSelRot)


    def deselect(self):
        canvas = self.iconMaster
        tags = canvas.itemcget(self.id, 'tags').split()
        NetworkNode.deselect(self)
        canvas.itemconfigure(self.innerBox, tags=tags,
                            image = self.imagetkRot)
        canvas.dtag(self.innerBox,'selected')
        

    def getColor(self):
        return (0.82, 0.88, 0.95, 0.5)


    def setColor(self, color):
        return

    
    def pickedComponent(self, x, y):
        xr = x - self.posx-self.shadowOffset[0] # x relative to image upper left corner
        yr = y - self.posy-self.shadowOffset[1] # y relative to image upper left corner

        # check if the (x,y) is the position of an input port
        for p in self.inputPorts:
            px, py = p.posRotated
            dx = abs(xr-px)
            dy = abs(yr-py)
            if dx<10 and dy<10:
                return p, 'input'

        # check if the (x,y) is the position of an output port
        for p in self.outputPorts:
            px, py = p.posRotated
            dx = abs(xr-px)
            dy = abs(yr-py)
            if dx<10 and dy<10:
                return p, 'output'

        # check if we clicked inside the node
        p1x, p1y, p2x, p2y = self.boxCorners
        #self.network.canvas.create_rectangle(p1x, p1y, p2x, p2y, outline='blue')
        angle = self.rotAngle
        if angle !=0.0:
            # unrotate the (x,y) point
            cx, cy = self.nodeCenter[0]+self.posx, self.nodeCenter[1]+self.posy
            x, y = rotateCoords((cx,cy), [x, y], angle)
            #self.network.canvas.create_rectangle(x-2, y-2, x+2, y+2, outline='red')
            
        if (x>=p1x and x<=p2x) and (y>=p1y and y<=p2y):
            # check if we picked resize handle
            #if (x-p1x<10 and y-p1y<10):
            #    print 'UL resize'
            #    return self, 'resize UL'
            if (p2x-x<10 and p2y-y<10):
                return self, 'resize'

            return self, 'node'

        return None, None


    def buildIcons(self, canvas, posx, posy, small=False):
        """Build NODE icon with ports etc"""
        NetworkNode.buildIcons(self, canvas, posx, posy, small)

        # add node editing menu entries
        self.menu.add_separator()
        self.menu.add_command(label='Rotate', command=self.rotate_cb)
        #self.menu.add_command(label='Resize', command=self.resize)

        self.stylesMenuTK = Tkinter.StringVar()
        self.stylesMenu = Tkinter.Menu(self.menu, tearoff=0,
                                       postcommand=self.fillStyleMenu)
        self.menu.add_cascade(label="styles", menu=self.stylesMenu)


    def fillStyleMenu(self, event=None):
        self.stylesMenu.delete(0, 'end')
        self.stylesMenu.add_command(label="Save As ...", command=self.saveStyle)
        self.stylesMenu.add_command(label="Set as Default",
                                    command=self.setDefaultStyle, state='disabled')

        self.stylesMenu.add_separator()

        self.stylesMenu.add_radiobutton(
            label='auto', variable=self.stylesMenuTK,
            command=self.setStyle_cb, value='auto')

        sm = self.editor.nodeStylesManager
        styles = sm.getStylesForNode(self)

        if styles:
            for name, style in styles.items():
                if name=='default': continue
                self.stylesMenu.add_radiobutton(
                    label=name, variable=self.stylesMenuTK,
                    command=self.setStyle_cb, value=name)
            if self.currentNodeStyle:
                self.stylesMenuTK.set(self.currentNodeStyle)

        if self.currentNodeStyle:
            # enable Set as Default menu entry
            self.stylesMenu.entryconfigure(1, state='normal')
        else:
            self.stylesMenuTK.set('')


    def setDefaultStyle(self):
        name = self.stylesMenuTK.get()
        self.editor.nodeStylesManager.setDefault(self, name)
        self.saveStylesDefinition()
        
        
    def setStyle_cb(self):
        name = self.stylesMenuTK.get()
        self.setStyle(name)

        
    def setStyle(self, name):
        if name == 'auto':
            self.currentNodeStyle = 'auto'
        else:
            sm = self.editor.nodeStylesManager
            styles = sm.getStylesForNode(self)
            self.nodeStyle.configure( **styles[name].getStyle() )
            self.currentNodeStyle = name
        self.redrawNode()


    def _saveStyle(self, result):
        #self.askNameWidget.withdraw()
        self.askNameWidget.deactivate()
        if result == 'OK':#  or hasattr(result, "widget"):
            name = self.askNameWidget.get()   
            style = self.nodeStyle.getStyle()
            sm = self.editor.nodeStylesManager
            sm.addStyle(self, name, NodeStyle(**style))
            self.currentNodeStyle = name
            self.saveStylesDefinition()


    def saveStyle(self):
        master = self.editor.root
        w = Pmw.PromptDialog(
            master, title = 'style name', 
            label_text = "Enter the name for this style",
            entryfield_labelpos = 'n',
            buttons = ('OK', 'Cancel'), command=self._saveStyle)
        sm = self.editor.nodeStylesManager
        styles = sm.getStylesForNode(self)
        if styles:
            nb = len(styles)+1
        else:
            nb = 1
        w.insertentry(0, "custom%d"%nb)
        w.component('entry').selection_range(0, Tkinter.END) 
        w.component('entry').focus_set()
        w.component('entry').bind('<Return>', self._saveStyle)
        w.geometry(
            '+%d+%d' % (master.winfo_x()+200,
                        master.winfo_y()+200))             
        self.askNameWidget = w
        w.activate()
        
        
    def drawNode(self, sx, sy, line, fill, macro, padding): 

        renderer = self.renderer

        # render the node shape
        renderer.makeNodeImage(sx, sy, line, fill, macro)
        self.UL = list(renderer.ul)
        # add ports
        #ip = self.inputPortsDescr
        #for pn in range(len(ip)):
        #    # find the position in image
        #    x, y , size, vector, line, fill, outline, label = ip.getDrawingParams(
        #        pn, self)
        #print 'ZZZZZZZZZZ', self.nodeStyle.iportNumToName

        ## def drawInputPort(port, portStyle):
        ##     port.vector = portStyle['vector']
        ##     port.vectorRotated = portStyle['vector']
        ##     x, y = self.nodeStyle.getPortXY(portStyle, self)
        ##     renderer.drawPort('in', x, y, portStyle)
        ##     port.posRotated = [x,y]
        ##     port.pos = (x,y)
            
        ## if macro:
        ##     pn = 0
        ##     for op in self.macroNetwork.ipNode.outputPorts[1:]:
        ##         ip = op.connections[0].port2
        ##         node = ip.node
        ##         portStyle = node.nodeStyle.inputPorts[ip.name]
        ##         print 'Drawing macro input', ip.name, portStyle
        ##         drawInputPort(ip, portStyle)
                
        ## else:
        ##     for pn, portName in enumerate(self.nodeStyle.iportNumToName):
        ##         if not self.widgetDescr.has_key(portName):
        ##             portStyle = self.nodeStyle.inputPorts[portName]
        ##             port = self.inputPorts[pn]
        ##             drawInputPort(port, portStyle)

        for pn, portName in enumerate(self.nodeStyle.iportNumToName):
            portStyle = self.nodeStyle.inputPorts[portName]
            port = self.inputPorts[pn]
            port.vector = portStyle['vector']
            port.vectorRotated = portStyle['vector']
            x, y = self.nodeStyle.getPortXY(portStyle, self)
            #edge = op[pn]['edge']
            #renderer.drawPort('out', x, y, size, vector, line, fill, outline, label, edge)
            renderer.drawPort('in', x, y, portStyle)
            port.posRotated = [x,y]
            port.pos = (x,y)
            
        #op = self.outputPortsDescr
        #for pn in range(len(op)):
        #    # find the position
        #    x, y, size, vector, line, fill, outline, label = op.getDrawingParams(
        #        pn, self)
        #    #print 'DRAWNODE1', self.name, pn, vector
        for pn, portName in enumerate(self.nodeStyle.oportNumToName):
            portStyle = self.nodeStyle.outputPorts[portName]
            port = self.outputPorts[pn]
            port.vector = portStyle['vector']
            port.vectorRotated = portStyle['vector']
            x, y = self.nodeStyle.getPortXY(portStyle, self)
            #edge = op[pn]['edge']
            #renderer.drawPort('out', x, y, size, vector, line, fill, outline, label, edge)
            renderer.drawPort('out', x, y, portStyle)
            port.posRotated = [x,y]
            port.pos = (x,y)

        renderer.drawLabel(self.name, padding)

        if self.iconFileName:
            filename = os.path.join(self.iconPath, self.iconFileName)
            renderer.drawIcon(filename)


    def getDefaultPortsStyleDict(self):
        ipStyles = []
        # count visible ports
        ct = 0
        for p in self.inputPortsDescr:
            if not self.widgetDescr.has_key(p['name']): ct += 1
        
        incr = 1.0/(ct+1)
        for n, pd in enumerate(self.inputPortsDescr):
            ipStyles.append( (pd['name'], {
                'ulrpos':((n+1)*incr,0), 'vector':(0,1), 'size':15,
                'fill':(1,1,1,1), 'line':(0.28, 0.45, 0.6, 1.), 'edge':'top',
                'outline':(0.28, 0.45, 0.6, 1.), 'label':pd['name'],
                }))
        opStyles = []
        incr = 1.0/(len(self.outputPortsDescr)+1)
        for n, pd in enumerate(self.outputPortsDescr):
            opStyles.append( (pd['name'], {
                'llrpos':((n+1)*incr,0), 'vector':(0,-1), 'size':15,
                'fill': (1,1,1,1), 'line':(0.28, 0.45, 0.6, 1.), 'edge':'bottom',
                'outline':(0.28, 0.45, 0.6, 1.), 'label':pd['name'],
                }))
        return ipStyles, opStyles


    def computeDefaultNodeSize(self):
        renderer = self.renderer
        ## compute the size needed for the node
        # get size of label
        x_bearing, y_bearing, width, height = renderer.getLabelSize(self.name)
        iconwidth = iconheight = 0
        if self.iconFileName:
            iconwidth = 20
            iconheight = 20 - 10 # -10 is minus the port label height
            width += iconwidth
            height += iconheight

        # here we compute how much space we need around the label for port icons and labels
        # port label are written using "Sans', size 10 which is 8 pixels heigh
        # for now we add 10 above the label and 10 below for the label
        # then we add maxPortSize / 2 above and below for the ports glyph
        # on the sides we will all the max of the port label length + 4 + max port glyph / 2
        maxPortSize = 0
        if self.iconFileName:
            maxPortLabLen = {'left':10, 'right':0, 'top':0, 'bottom':0}
            maxPortLabHeight = {'left':0, 'right':0, 'top':10, 'bottom':0}
        else:
            maxPortLabLen = {'left':0, 'right':0, 'top':0, 'bottom':0}
            maxPortLabHeight = {'left':0, 'right':0, 'top':0, 'bottom':0}

        sumPortLabLenTop = 0.0
        sumPortLabLenBottom = 0.0

        for pn, port in enumerate(self.inputPorts):
            if self.widgetDescr.has_key(port.name): continue
            pd = self.nodeStyle.inputPorts[port.name]
            edge = pd['edge']
            size = pd['size']
            label = pd['label']
            if size > maxPortSize: maxPortSize=size
            if label:
                x_b, y_b, w, h = renderer.getLabelSize(label, 'Sans', size=10)
                if edge=='top':
                    sumPortLabLenTop += w+10
                elif edge=='bottom':
                    sumPortLabLenBottom += w+10
                if w > maxPortLabLen[edge]: maxPortLabLen[edge] = w
                if h > maxPortLabHeight[edge]: maxPortLabHeight[edge] = h

        for pn, port in enumerate(self.outputPorts):
            pd = self.nodeStyle.outputPorts[port.name]
            edge = pd['edge']
            size = pd['size']
            label = pd['label']
            if size > maxPortSize: maxPortSize=size
            if label:
                x_b, y_b, w, h = renderer.getLabelSize(label, 'Sans', size=10)
                if edge=='top':
                    sumPortLabLenTop += w+10
                elif edge=='bottom':
                    sumPortLabLenBottom += w+10
                if w > maxPortLabLen[edge]: maxPortLabLen[edge] = w
                if h > maxPortLabHeight[edge]: maxPortLabHeight[edge] = h
            
        pady = maxPortLabHeight['top'] + maxPortLabHeight['bottom'] + maxPortSize + 2*8
        padx = maxPortLabLen['left'] + maxPortLabLen['right'] + maxPortSize + 2*8

        padding = {
            'left': max(5, maxPortLabLen['left']),
            'right': max(5, maxPortLabLen['right']),
            'top': max(5, maxPortLabHeight['top']),
            'bottom': max(5, maxPortLabHeight['bottom'])
            }

        sx = max( max(width, sumPortLabLenTop, sumPortLabLenBottom) + iconwidth + 2*8,
                  max(maxPortLabLen['bottom'], maxPortLabLen['top'], ))
        sy = height+pady
        #print 'GGGGG', maxPortSize, maxPortLabLen, maxPortLabHeight, width, height, padx, pady, sx, sy
        return sx, sy, padding

    
    def makeNodeImage(self, canvas, posx, posy):
        renderer = self.renderer
        if self.nodeStyle is None: # no styles defined. Happens when we first
                                   # click on a node in the tree
            #print 'NO NodeStyle', self.library
            if self.library is not None:
                color1 = self.library.fillColor
                color2 = self.library.outlineColor
            else:
                color1 = '#FFFFFF'
                color2 = '#AAAAAA'
            fillColor = [float(x)/256**2 for x in
                         self.iconMaster.winfo_rgb(color1)]
            outlineColor = [float(x)/256**2 for x in
                         self.iconMaster.winfo_rgb(color2)]
            sm = self.editor.nodeStylesManager
            stylesDict = sm.getStylesForNode(self)
            if stylesDict is None or stylesDict['default']=='auto': # no style available for this class
                #print '  no style dict'
                # create node Style because it will be used in computeDefaultNodeSize
                self.nodeStyle = style = NodeStyle(
                    width=200, height=200, fillColor=fillColor,
                    outlineColor=outlineColor)
                ipStyles, opStyles = self.getDefaultPortsStyleDict()
                style.setInputPortStyles(ipStyles)
                style.setOutputPortStyles(opStyles)
                sx, sy, padding = self.computeDefaultNodeSize()
                style.configure(width=sx, height=sy)
                #self.currentNodeStyle = None #'auto'
                self.currentNodeStyle = 'auto'
            else:
                #print ' with style dict'
                default = stylesDict['default']
                style = stylesDict[default].copy()
                self.currentNodeStyle = default
                self.nodeStyle = style
                sx, sy, padding = self.computeDefaultNodeSize()


        elif self.currentNodeStyle == 'auto':
            #print 'Auto NodeStyle'
            # call to compute padding
            sx, sy, padding = self.computeDefaultNodeSize()
            style = self.nodeStyle = NodeStyle(width=sx, height=sy)
            ipStyles, opStyles = self.getDefaultPortsStyleDict()
            style.setInputPortStyles(ipStyles)
            style.setOutputPortStyles(opStyles)
        else:
            #print 'WITH NodeStyle'
            # call to compute padding
            sx, sy, padding = self.computeDefaultNodeSize()
            
        sx, sy = self.nodeStyle.getSize()

        self.activeWidth = sx
        self.activeHeight = sy
        
        # render the node shape
        fill = self.nodeStyle.getFillColor()
        line = self.nodeStyle.getOutlineColor()
        rotAngle = self.nodeStyle.getAngle()
        #print 'ANGLE', self.nodeStyle.getAngle()
        
        from NetworkEditor.macros import MacroImageNode
        macro = isinstance(self, MacroImageNode)

        # draw the node
        self.drawNode(sx, sy, line, fill, macro, padding)        

        image = renderer.getPilImage()
        self.imShadow1, offset = renderer.addDropShadow()
        self.shadowOffset = offset
        #self.imShadow1 = image
        self.imagetk = ImageTk.PhotoImage(image=self.imShadow1)
        self.imagetkRot = self.imagetk
        self.imwidth = self.imagetk.width()
        self.imheight = self.imagetk.height()

        self.boxCorners = self.getBoxCorners()

        # assign ports posx and posy
        for port in self.inputPorts+self.outputPorts:
            x,y = port.pos
            port.posx = posx + self.shadowOffset[0] + x
            port.posy = posy + self.shadowOffset[0] + y
            
        canvas.itemconfigure(self.innerBox, image=self.imagetk)

        # draw image outline
        #bb = canvas.bbox(self.innerBox)
        #canvas.create_rectangle(*bb, outline='black')
     
        ## this could be used to render selected nodes
        # draw rectangle around node image bbox
##         x1, y1, x2, y2 = renderer.bbox
##         self.nodeOutline = canvas.create_rectangle(
##             x1+posx, y1+posy, x2+posx, y2+posy, fill='yellow',
##             outline='yellow', tags=(self.iconTag,'node'))

        ## build an image with yellow background for selected state        
        fill = (1., 1, 0., 0.5)
        line = (0.28, 0.45, 0.6, 1.)
        self.drawNode(sx, sy, line, fill, macro, padding)        
        self.imShadow2, offset = renderer.addDropShadow()
        #self.imShadow2 = image
        self.imagetkSel = ImageTk.PhotoImage(image=self.imShadow2)
        self.imagetkSelRot = self.imagetkSel

        bb = canvas.bbox(self.innerBox)
        self.nodeCenter = (bb[2]-bb[0])*.5, (bb[3]-bb[1])*.5
        #self.nodeCenter = (sx*.5, sy*.5)

        #print 'ROTATE', rotAngle, self.rotAngle
        self.rotate(rotAngle)


    def buildNodeIcon(self, canvas, posx, posy, small=False):
        renderer = self.renderer
        self.iconMaster = canvas
        
        # set posx, posy
        self.posx = posx
        self.posy = posy

        self.innerBox = canvas.create_image(
            posx, posy, anchor=Tkinter.NW, # image=self.imagetk,
            tags=(self.iconTag,'node'))

        self.makeNodeImage(canvas, posx, posy)

        self.outerBox = self.innerBox
        bb = canvas.bbox(self.innerBox)

        #print 'NODE IMAGE BBOX', bb, posx, posy, self.UL, self.activeWidth, self.activeHeight, self.shadowOffset
        # draw node's image bounding box
        #canvas.create_rectangle(
        #    *bb, fill='', outline='yellow', tags=(self.iconTag,'node'))
        
        # draw node's box bounding box
        #canvas.create_rectangle(
        #    bb[0]+self.UL[0]+self.shadowOffset[0],
        #    bb[1]+self.UL[1]+self.shadowOffset[1],
        #    bb[0]+self.UL[0]+self.shadowOffset[0]+self.activeWidth,
        #    bb[1]+self.UL[1]+self.shadowOffset[1]+self.activeHeight,
        #   fill='', outline='green', tags=(self.iconTag,'node'))

        #self.nodeCenter = (bb[2]-bb[0])*.5, (bb[3]-bb[1])*.5
        
        self.textId = self.innerBox
        self.id = self.innerBox # used to build network.nodesById used for picking
        self.iconTag = 'node'+str(self.textId) # used in node.select

        #if self.network is not None:
        #    self.move(posx, posy)
        self.hasMoved = False # reset this attribute because the current
                              # position is now the original position


    ##
    ## functions used to rotate Nodes
    ##
    def rotateRelative(self, angle):
        canvas = self.iconMaster
        self.rotAngle = (self.rotAngle + angle)%360

        # center of unrotated image
        cx, cy = self.nodeCenter

        # rotate node images
        imShadowRotated = self.imShadow1.rotate(
            self.rotAngle, Image.BICUBIC, expand=1)
        self.imagetkRot = ImageTk.PhotoImage(image=imShadowRotated)

        imShadowRotated = self.imShadow2.rotate(
            self.rotAngle, Image.BICUBIC, expand=1)
        self.imagetkSelRot = ImageTk.PhotoImage(image=imShadowRotated)
        
        canvas.itemconfigure(self.innerBox, image=self.imagetkRot)
        bb = canvas.bbox(self.innerBox)
        #bb = self.boxCorners
        rcx, rcy = (bb[2]-bb[0])*.5, (bb[3]-bb[1])*.5
        
        canvas.coords(self.innerBox, self.posx+cx-rcx, self.posy+cy-rcy)
        
        # rotate input ports
        # node center in canvas coordinate system
        cx = self.posx + self.nodeCenter[0]
        cy = self.posy + self.nodeCenter[1]
        # node uper left corner in canvas coordinate system
        offx = self.posx+self.shadowOffset[0]
        offy = self.posy+self.shadowOffset[1]
        for p in self.inputPorts:
            hpx = p.pos[0]+offx
            hpy = p.pos[1]+offy
            hpxr, hpyr = rotateCoords( (cx, cy), (hpx, hpy), -self.rotAngle)
            p.posRotated = (hpxr-offx, hpyr-offy)
            # display hotspots
            #canvas.create_rectangle(hpxr-5, hpyr-5, hpxr+5, hpyr+5)

            a,b,c,d = rotateCoords( (cx, cy), (0, 0, p.vector[0], p.vector[1]),
                                    self.rotAngle)
            p.vectorRotated = [c-a, d-b]
            
        # rotate output ports
        for p in self.outputPorts:
            hpx = p.pos[0]+offx
            hpy = p.pos[1]+offy
            hpxr, hpyr = rotateCoords( (cx, cy), (hpx, hpy), -self.rotAngle)
            p.posRotated = (hpxr-offx, hpyr-offy)
            # draw rectangel on hotspot for debuging
            #canvas.create_rectangle(hpxr-5, hpyr-5, hpxr+5, hpyr+5)

            a,b,c,d = rotateCoords( (cx, cy), (0, 0, p.vector[0], p.vector[1]),
                                    self.rotAngle)
            p.vectorRotated = [c-a, d-b]
            #print p.vector, a,b,c,d, p.vectorRotated
            
        
    def rotate(self, absoluteAngle):
        angle = absoluteAngle-self.rotAngle
        self.rotateRelative(angle)
        

    def rotate_cb(self):
        canvas = self.iconMaster
        bb = canvas.bbox(self.innerBox)
        # posx and pos y are upper left corner
        # self.nodeCenter is center of node relative to posx, posy
        cx = self.posx+self.nodeCenter[0]
        cy = self.posy+self.nodeCenter[1]
        
        rad = 0.5*max(bb[2]-bb[0], bb[1]-bb[0])+10

        #draw a circle with an arrow to indicate node rotation mode
        arcid = canvas.create_oval( cx-rad, cy-rad, cx+rad, cy+rad, 
                                    outline='green', width=2.0, tags=('arc',))
        self._arcid = arcid
        canvas.tag_bind(arcid, "<ButtonPress-1>", self.startRotate_cb)
        
        
    def startRotate_cb(self, event=None):
        canvas = self.iconMaster
        self._x0 = canvas.canvasx(event.x) - self.posx - self.nodeCenter[0]
        self._y0 = canvas.canvasy(event.y) - self.posy - self.nodeCenter[1]
        #self._deltaAngle = 0
        canvas.itemconfigure(self._arcid, outline='red')
        canvas.tag_bind(self._arcid, "<Motion>", self.moveToRotate_cb)
        canvas.tag_bind(self._arcid, "<ButtonRelease-1>", self.endRotate_cb)
        #self._lineid = canvas.create_line(
        #    self.posx + self.nodeCenter[0], self.posy + self.nodeCenter[1],
        #    canvas.canvasx(event.x), canvas.canvasy(event.y),
        #    fill='green', width=2.0, tags=('arc',))
        self._textid = canvas.create_text( 
            canvas.canvasx(event.x)+10, canvas.canvasy(event.y)-10,
            text='%d'%self.rotAngle, fill='black', tags=('arc',))

        
    def fullAngle(self, x0, y0, x1, y1):
        n0 = math.sqrt(x0*x0 + y0*y0)
        n1 = math.sqrt(x1*x1 + y1*y1)
        x0 = x0/n0
        y0 = y0/n0
        x1 = x1/n1
        y1 = y1/n1
        tetha = math.acos( (x0*x1 + y0*y1))
        if x0*y1-y0*x1 > 0:
            return math.degrees(tetha)
        else:
            return math.degrees(2*math.pi-tetha)


    def moveToRotate_cb(self, event=None):
        canvas = self.iconMaster
        x1 = canvas.canvasx(event.x) - self.posx - self.nodeCenter[0]
        y1 = canvas.canvasy(event.y) - self.posy - self.nodeCenter[1]
        #canvas.coords(
        #    self._lineid, self.posx + self.nodeCenter[0],
        #    self.posy + self.nodeCenter[1],
        #    canvas.canvasx(event.x), canvas.canvasx(event.y))
        angle = self.fullAngle(self._x0, -self._y0, x1, -y1)
        self.rotate(15*int(angle/15))
        canvas.itemconfigure(self._textid, text='%d'%self.rotAngle)
        canvas.coords(self._textid, canvas.canvasx(event.x)+10,
                      canvas.canvasx(event.y)-10)

        for p in self.inputPorts:
            for c in p.connections:
                c.updatePosition()

        for p in self.outputPorts:
            for c in p.connections:
                c.updatePosition()


    def endRotate_cb(self, event=None):
        canvas = self.iconMaster
        self.iconMaster.delete('arc')
        self.nodeStyle.configure(rotAngle=self.rotAngle)
        self.currentNodeStyle = None # set the a style name that is a key in
        del self._arcid
        del self._x0
        del self._y0
    

    def updatePosXPosY(self, dx, dy):
        """set node.posx and node.posy after node has been moved"""
        self.posx += dx
        self.posy += dy
        self.boxCorners = self.getBoxCorners()


    def getBoxCorners(self):
        dx, dy = self.UL
        sx, sy = self.shadowOffset
        p1x, p1y = self.posx + dx + sx, self.posy + dy + sy,
        p2x = self.posx + dx + sx + self.activeWidth
        p2y =  self.posy + dy + sy + self.activeHeight
        return p1x, p1y, p2x, p2y

    ##
    ## functions used to move ports
    ##
    def segmentIntersection(self, p0, p1):
        canvas = self.iconMaster

        # center of unrotated image
        cx, cy = self.nodeCenter[0]+self.posx, self.nodeCenter[1]+self.posy
        p1x, p1y, p2x,p2y = self.boxCorners
        coords = (p1x, p1y, p2x, p1y, p2x, p2y, p1x, p2y, p1x, p1y)
        
        # rotate coords of the box box
        coords  = rotateCoords((cx,cy), coords, -self.rotAngle)

        l = len(coords)
        for i in range(0, l, 2):
            p2 = (coords[i], coords[i+1])
            p3 = (coords[(i+2)%l], coords[(i+3)%l])
            xi, yi = seg_intersect(p0, p1, p2, p3)
            inSegment( (xi, yi), p2, p3)
            if inSegment( (xi, yi), p0, p1) and inSegment( (xi, yi), p2, p3):
                #print 'intersection with edge', i, p0, p1, p2, p3, xi, yi
                return xi,yi
        return None, None


    def movePortTo(self, port, x, y):
        # x.y are absolute coordinates on the canvas and are expected to be
        # on the node's box outline
        #
        # x and y are potentially on the rotated shape of the box
        # we undo the rotation to set the port description, re-create the image
        # and rotate the node

        #print 'MOVE PORT TO', x, y
        angle = self.rotAngle
        if angle !=0.0:
            # unrotate the (x,y) point
            cx, cy = self.nodeCenter[0]+self.posx, self.nodeCenter[1]+self.posy
            x, y = rotateCoords((cx,cy), [x,y], self.rotAngle)

        # find the port's style description
        from ports import ImageInputPort, ImageOutputPort
        if isinstance(port, ImageInputPort):
            name = self.nodeStyle.iportNumToName[port.number]
            pd = self.nodeStyle.inputPorts[name]
        else:
            name = self.nodeStyle.oportNumToName[port.number]
            pd = self.nodeStyle.outputPorts[name]
            
        #print 'BEFORE', pd
        # now remove the **rpos entry
        for k,v in pd.items():
            if k[-4:]=='rpos':
                print k, pd[k]
                del pd[k]

        width = float(self.activeWidth)
        height = float(self.activeHeight)

        p1x, p1y, p2x, p2y = self.getBoxCorners()
        #print p1x, p1y, p2x, p2y
        if abs(x-p1x)<2: # left edge
            pd['ulrpos'] = (0, (y-p1y)/height)
            pd['vector'] = (-1, 0)
            #print 'ulrpos1', (x-p1x, y-p1y)
        elif abs(x-p2x)<2: # right edge
            pd['lrrpos'] = (0, (y-p2y)/height)
            pd['vector'] = (1, 0)
            #print 'lrrpos2', (x-p2x, y-p2y)
        elif abs(y-p1y)<2: # top edge
            pd['ulrpos'] = ((x-p1x)/width, 0)
            pd['vector'] = (0, 1)
            #print 'ulrpos1', (x-p1x, y-p1y), vector
        elif abs(y-p2y)<2: # bottom edge
            pd['lrrpos'] = ((x-p2x)/width, 0)
            pd['vector'] = (0, -1)
            #print 'lrrpos2', (x-p2x, y-p2y)
        else:
            print "ERROR: edge not found", x, y, p1x, p1y, p2x, p2y

        pd['edge'] = self.nodeStyle.getEdge(pd)

        #print 'AFTER', id(pd), pd
        
        self.rotate(angle)
            
        self.redrawNode()

        port._hasMoved = True


    def rename(self, name, tagModified=True):
        """Rename a node. remember the name has changed, resize the node if
necessary"""
        if name == self.name or name is None or len(name)==0:
            return
        # if name contains ' " remove them
        name = name.replace("'", "")
        name = name.replace('"', "")
        
        self.name=name
        self.redrawNode()
        if tagModified is True:
            self._setModified(True)


    def redrawNode(self):
        self.makeNodeImage(self.iconMaster, self.posx, self.posy)
        
        # update all connections
        for port in self.inputPorts+self.outputPorts:
            for c in port.connections:
                if c.id:
                    c.updatePosition()


    def movePortToRelativeLocation(self, port, corner, dx, dy):
        # move a port to a position relative to one of its corners
        # corner can be ul, ll, ur, or lr string
        # dx, dy are relative displacements from the corner point

        p1x, p1y, p2x,p2y = self.boxCorners
        if corner=='ul':
            cornerx, cornery = p1x, p1y
        elif corner=='ll':
            cornerx, cornery = p1x, p2y
        elif corner=='ur':
            cornerx, cornery = p2x, p1y
        elif corner=='lr':
            cornerx, cornery = p2x, p2y

        self.movePortTo(port, cornerx+dx, cornery+dy) 


    def movePortToRelativePos(self, port, corner, edge, percentx, percenty):
        # move a port to a position specified by a corner and a percent of edge length

        angle = self.rotAngle
        if angle !=0.0:
            # unrotate the (x,y) point
            cx, cy = self.nodeCenter[0]+self.posx, self.nodeCenter[1]+self.posy
            x, y = rotateCoords((cx,cy), [x,y], self.rotAngle)

        # find the port's style description
        from ports import ImageInputPort, ImageOutputPort
        if isinstance(port, ImageInputPort):
            name = self.nodeStyle.iportNumToName[port.number]
            pd = self.nodeStyle.inputPorts[name]
        else:
            name = self.nodeStyle.oportNumToName[port.number]
            pd = self.nodeStyle.outputPorts[name]

        ## # find the port's description
        ## found = False
        ## for p, pd in zip(self.inputPorts, self.inputPortsDescr):
        ##     if p==port:
        ##         found = True
        ##         break

        ## if not found:
        ##     for p, pd in zip(self.outputPorts, self.outputPortsDescr):
        ##         if p==port:
        ##             found = True
                    ## break
        # now remove the **rpos entry
        for k,v in pd.items():
            if k[-4:]=='rpos':
                del pd[k]

        p1x, p1y, p2x,p2y = self.boxCorners
        width = p2x-p1x
        height = p2y-p1y
        if corner=='ul':
            pd['ulrpos'] = (percentx, percenty)
        elif corner=='ll':
            pd['llrpos'] = (percentx, percenty)
        elif corner=='ur':
            pd['urrpos'] = (percentx, percenty)
        elif corner=='lr':
            pd['lrrpos'] = (percentx, percenty)
        
        if edge=='left':
            pd['vector'] = (-1, 0)
        elif edge=='right':
            pd['vector'] = (1, 0)
        elif edge=='top':
            pd['vector'] = (0, 1)
        elif edge=='bottom':
            pd['vector'] = (0, -1)
            
        self.makeNodeImage(self.iconMaster, self.posx, self.posy)

        self.rotate(angle)
            
        # update all connections
        for p in self.inputPorts+self.outputPorts:
            for c in p.connections:
                if c.id:
                    c.updatePosition()

        port._hasMoved = True

#n = WarpIV.ed.currentNetwork.nodes[0]


class ImageDataNode(ImageNode):
    """
    Subclass ImageNode to render a node as a circle with an input at the top
    and an output at the bottom (use for WarpIV data
    """
    def drawMapIcon(self, naviMap):
        canvas = naviMap.mapCanvas
        x0, y0 = naviMap.upperLeft
        scaleFactor = naviMap.scaleFactor
        c = self.getBoxCorners()
        cid = canvas.create_rectangle(
            [x0+c[0]*scaleFactor, y0+c[1]*scaleFactor,
             x0+c[2]*scaleFactor, y0+c[3]*scaleFactor],
            fill='grey50', outline='black', tag=('navimap',))
        ## import Image
        ## im = self.imShadow1
        ## self.scaledImage = im.resize((int(im.size[0]*scaleFactor),
        ##                               int(im.size[1]*scaleFactor)), Image.ANTIALIAS)
        ## self.mapImagetk = ImageTk.PhotoImage(image=self.scaledImage)
        ## cid = canvas.create_image( x0+self.posx*scaleFactor, y0+self.posy*scaleFactor,
        ##                            image=self.mapImagetk)
        self.naviMapID = cid
        return cid


    def getDefaultPortsStyleDict(self):
        ipStyles = []

        ipStyles.append( ('name', {
                'ulrpos':(0.1,0), 'vector':(0,1), 'size':15,
                'fill':(1,1,1,1), 'line':(0.28, 0.45, 0.6, 1.), 'edge':'top',
                'outline':(0.28, 0.45, 0.6, 1.), 'label':'name',
                }))
        ipStyles.append( ('value', {
                'ulrpos':(0.5,0), 'vector':(0,1), 'size':15,
                'fill':(1,1,1,1), 'line':(0.28, 0.45, 0.6, 1.), 'edge':'top',
                'outline':(0.28, 0.45, 0.6, 1.), 'label':'value',
                }))
        opStyles = []
        opStyles.append( ('output1', {
                'llrpos':(0.5,0), 'vector':(0,-1), 'size':15,
                'fill': (1,1,1,1), 'line':(0.28, 0.45, 0.6, 1.), 'edge':'bottom',
                'outline':(0.28, 0.45, 0.6, 1.), 'label':'output1',
                }))
        return ipStyles, opStyles


    def drawNode(self, sx, sy, line, fill, macro, padding): 
        renderer = self.renderer

        self.activeWidth = sx
        self.activeHeight = sy
        border = renderer.border
        
        renderer.makeCircleNodeImage(sx, sy, line, fill, macro)
        self.UL = list(renderer.ul)
        
        port = self.inputPorts[1] # only draw second port for value
        portStyle = self.nodeStyle.inputPorts[port.name]
        port.vector = portStyle['vector']
        port.vectorRotated = portStyle['vector']
        x, y = self.nodeStyle.getPortXY(portStyle, self)
        #print 'ZZZZZZZ', x, y, border+sx*.5
        #x, y = border+sx*.5, border+portStyle.get('size', 10)*.5
        portStyle['label'] = None
        renderer.drawPort('in', x, y, portStyle)
        port.posRotated = [x,y]
        port.pos = (x,y)

        port = self.outputPorts[0]
        portStyle = self.nodeStyle.outputPorts[self.outputPorts[0].name]
        port.vector = portStyle['vector']
        port.vectorRotated = portStyle['vector']
        x, y = self.nodeStyle.getPortXY(portStyle, self)
        #x, y = border+sx*.5, border+sy-portStyle.get('size', 10)*.5
        portStyle['label'] = None
        renderer.drawPort('out', x, y, portStyle)
        port.posRotated = [x,y]
        port.pos = (x,y)

        padding = {'left':5, 'top':0, 'right':5, 'bottom':5}
        renderer.drawLabel(self.name, padding)
