#########################################################################
#
# Date: Nov. 2012  Author: Michel Sanner
#
#       sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################

from NetworkEditor.net import AddNodeEvent, ConnectNodes, \
     DeleteNodesEvent, DeleteConnectionsEvent
from mglutil.util.callback import CallbackFunction
import weakref

class NavigationMap:
    """
    draw a small representation of the total canvas area with a rectangle
    showing the outline of the visible portion of the map
    """

    def __init__(self, network, scrolledCanvas, mapCanvas, scaleFactor=0.05):

        self.network = weakref.ref(network)
        editor = network.editor
        self.editor = weakref.ref(editor)
        self.mapCanvas = mapCanvas # where we draw the map
        self.sc_canvas = scrolledCanvas # where the network
        self.scaleFactor = scaleFactor
        canvas = self.netCanvas = scrolledCanvas.component('canvas')
        # find total size of the canvas
        bbox = map(int, canvas.configure('scrollregion')[-1])
        # compute map width and height
        self.width = (bbox[2]-bbox[0])*scaleFactor
        self.height = (bbox[3]-bbox[1])*scaleFactor
        self.upperLeft = (0,0)

        # override callback for scroll bar to moce map to keep
        # it in the upperLeft corner of the Network
        cb = CallbackFunction(self.moveMapx, 'y')
        scrolledCanvas.component('vertscrollbar').configure(command=cb)
        cb = CallbackFunction(self.moveMapx, 'x')
        scrolledCanvas.component('horizscrollbar').configure(command=cb)

        # register interest in event that add items to the minimap
        editor.registerListener(AddNodeEvent, self.handleAddNode)
        editor.registerListener(ConnectNodes, self.handleConnectNodes)
        editor.registerListener(DeleteNodesEvent, self.handleDeleteNodes)
        editor.registerListener(DeleteConnectionsEvent,
                                self.handleDeleteConnections)

        # create navi map outline
        self.outlineCID = canvas.create_rectangle(
            0, 0, self.width, self.height,  outline='black', tags=('navimap',))

        # draw visible window outline
        self.visibleWinOutlineCID = canvas.create_rectangle(
            0, 0, 10, 10, outline='blue', width=2,
            tags=('navimap','visibleWin',))
        mapCanvas.tag_bind(self.visibleWinOutlineCID,
                           "<ButtonPress-1>", self.moveVisibleWin_cb)
        canvas.tag_bind(self.visibleWinOutlineCID,
                        "<B1-Motion>", self.moveCanvas)
        canvas.tag_bind(self.visibleWinOutlineCID,
                        "<ButtonRelease-1>", self.moveCanvasEnd)

    def __del__(self):
        self.unregisterCallBacks()

        
    def unregisterCallBacks(self):
        editor = self.editor()
        editor.unregisterListener(AddNodeEvent, self.handleAddNode)
        editor.unregisterListener(ConnectNodes, self.handleConnectNodes)
        editor.unregisterListener(DeleteNodesEvent, self.handleDeleteNodes)
        editor.unregisterListener(DeleteConnectionsEvent,
                                  self.handleDeleteConnections)
        
        
    def moveVisibleWin_cb(self, event):
        self.lastx = event.x
        self.lasty = event.y
        canvas = self.mapCanvas
        canvas.configure(cursor='hand2')
        canvas.itemconfigure(self.visibleWinOutlineCID, outline='green')
        

    def moveCanvas(self, event=None):
        ed = self.editor()
        dx = (event.x - self.lastx)/self.scaleFactor
        dy = (event.y - self.lasty)/self.scaleFactor
        canvas = self.netCanvas
        xo = max(0, canvas.canvasx(0)+dx)
        yo = max(0, canvas.canvasy(0)+dy)

        canvas.xview_moveto(xo/float(ed.totalWidth))
        canvas.yview_moveto(yo/float(ed.totalHeight))
	self.lastx = event.x
        self.lasty = event.y

        self.moveMapx(None, None, None)

        canvas.update_idletasks()
    
    
    def moveCanvasEnd(self, event=None):
        num = event.num
        canvas = self.mapCanvas
        canvas.configure(cursor='')


    def placeVisibleWin(self):
        if self.network().showNaviMap:
            netCanvas = self.netCanvas
            mapCanvas = self.mapCanvas
            width = netCanvas.winfo_width()
            height = netCanvas.winfo_height()
            if width==1 or height==1:
                netCanvas.after(100, self.placeVisibleWin)

            x0 = netCanvas.canvasx(0)
            y0 = netCanvas.canvasy(0)
            sc = self.scaleFactor
            mapCanvas.coords(self.visibleWinOutlineCID, x0+x0*sc, y0+y0*sc,
                             x0+(x0+width)*sc, y0+(y0+height)*sc)
            mapCanvas.itemconfigure(self.visibleWinOutlineCID, outline='blue')
        

    def moveMapx(self, direction, how, *args):
        # call default callback to scroll canvas
        canvas = self.netCanvas
        if direction=='y':
            canvas.yview(how, *args)
        elif direction=='x':
            canvas.xview(how, *args)

        # canvas coords of upper left corner of visible part
        x = canvas.canvasx(0)
        y = canvas.canvasy(0)
        x0, y0 = self.upperLeft
        canvas.move('navimap', x-x0, y-y0)
        self.upperLeft = (x, y)
        
        self.placeVisibleWin()

    ##
    ##  do not use self.mapCanvas but instead use object.network.naviMap as
    ##  ed.refreshNet_cb will recreate a new NaviMap which will be diffrent
    ##  from the one register in the call back
    ##
    def handleAddNode(self, event):
        n = event.node
        naviMap = n.network.naviMap
        if n.network == naviMap.network():
            n.drawMapIcon(naviMap)


    def handleConnectNodes(self, event):
        c = event.connection
        naviMap = c.network.naviMap
        if c.network == naviMap.network():
            c.drawMapIcon(c.network.naviMap)


    def handleDeleteNodes(self, event):
        for n in event.nodes:
            naviMap = n.network.naviMap
            if n.network != naviMap.network():
                continue # this node is not on this map
            mapCanvas = naviMap.mapCanvas
            mapCanvas.delete(n.naviMapID)
            for p in n.inputPorts:
                for c in p.connections:
                    mapCanvas.delete(c.naviMapID)
            for p in n.outputPorts:
                for c in p.connections:
                    mapCanvas.delete(c.naviMapID)
    

    def handleDeleteConnections(self, event):
        for c in event.connection:
            naviMap = c.network.naviMap
            if c.network == naviMap.network():
                c.network.naviMap.mapCanvas.delete(c.naviMapID)


    def printEvent(self, event):
        print event


    def clearMap(self):
        pass
    
