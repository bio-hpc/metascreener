#########################################################################
#
# Date: Nov. 2012  Author: Michel F. Sanner
#
#       sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel F. Sanner and TSRI
#   

#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Vision/libTree.py,v 1.8 2013/08/21 21:09:09 sanner Exp $
#
# $Id: libTree.py,v 1.8 2013/08/21 21:09:09 sanner Exp $
#
import Tkinter, Pmw, ImageTk, TkTreectrl, tkFont, weakref, numpy, random, weakref, os, Vision

from NetworkEditor.items import NetworkNode
from Vision.VPE import NodeLibrary, NodeProxy

ICONPATH = os.path.join(Vision.__path__[0], 'Icons')

class ScrolledFormatedText(Pmw.ScrolledText):
    """
    class to render tet and images in a Tk widget

    It is subclassing a Pmw.ScrolledText to add the ability to annotate
    text with formatting information similar to HTML

    The basic idea is to attach tags to portions of the text and associate a format
    with the tag. For instance <B>Title<\B> will render the word Title using a Boold font.

    Tags can be added by calling addTag(tag, name, cfg) where tab is what you put in your text
    name is the name of the tag in Tk and cfg are the formating options associated with this tag.
    For instance the <H1> tag is added as follows:
        addTag('H1', 'Header1', {'font':(font, size+4, 'bold'),
                                 'spacing1':10, 'spacing3': 10, 'foreground':'#265d94'})

    a formatted string can be displayed by calling renderText(formattedString)

    CAVEAT: if multiple tags are attached to a range of text style options from the most recently
    created tag override options from earlier tag. This could possibly be overcome by creating a
    dybnamic tag on the fly that merges the 2 style !
    """
    def __init__(self, master, *args, **kw):

        self.master = master
        Pmw.ScrolledText.__init__(self, master, *args, **kw)
        self.tkText = self.component('text')
        # dictionary where keys are tags and values are tagnames
        self.tagDict = {}

        f = self.font = 'Arial'
        s = self.size = 10

        self.addTag('B', 'bold', {'font':(f, s, 'bold')})
        self.addTag('I', 'italic', {'font':(f, s, 'italic')})
        self.addTag('U', 'underline', {'font':(f, s, 'underline')})
        self.addTag('R', 'roman', {'font':(f, s, 'roman')})
        self.addTag('O', 'overstrike', {'font':(f, s, 'overstrike')})
        self.addTag('H1', 'Header1', {'font':(f, s+4, 'bold'),
                    'spacing1':10, 'spacing3': 10, 'foreground':'#265d94'})
        self.addTag('H2', 'Header2', {'font':(f, s+2, 'bold'),
                    'spacing1':5, 'spacing3': 5, 'lmargin1':15, 'foreground':'#265d94'})
        self.addTag('H3', 'Header3', {'font':(f, s, 'underline'), 'foreground':'#265d94',
                    'spacing1':5, 'spacing3': 5, 'lmargin1':30, 'lmargin2':30})


    def addTag(self, tag, name, cfg):
        self.tagDict[tag] = name
        self.tkText.tag_add(name, '0.0', '0.0') # create the tag in Tk.Text
        self.tkText.tag_configure(name, **cfg)

        
    def renderText(self, textStr):
        text = self.tkText
        tags = []
        i = 0
        while i<len(textStr):
            try:
                end = i+textStr[i:].index('<')
            except ValueError:
                end = -1
            cstr = textStr[i:end]
            #print 'Print', cstr, tags
            text.insert('end', cstr, tuple(tags))
            i += len(cstr) + 1 # to pass '<'
            if i>=len(textStr): break
            tagStr = textStr[i:i+textStr[i:].index('>')]
            if tagStr[0]=='\\': # end of tag
                tags.remove(self.tagDict[tagStr[1:]])
                #print 'remove tag', tagStr[1:]
            else:
                tags.append(self.tagDict[tagStr])
                #print 'add tag', tagStr
            i += len(tagStr) + 1


class Node:

    def __init__(self, name='Libraries', object=None):
        self.children = []
        self.object = object
        self.name=name
        
    def addChild(self, node):
        self.children.append(node)
        

class LibTree:

    modelTreeIcon = ImageTk.PhotoImage(file=os.path.join(ICONPATH, 'model.png'))
    systemTreeIcon = ImageTk.PhotoImage(file=os.path.join(ICONPATH, 'system.png'))
    
    def __init__(self, editor, master=None):
        if master is None:
            master = Tkinter.Tk()
            self.ownsRoot = True
        else:
            self.ownsRoot = False
        
        self.treeStyles = {'library':{}, 'category':{}, 'model':{}, 'system':{}}
        self.treeHeight = 300
        self.docHeight = 300
        self.createTree(master)
        self.editor = weakref.ref(editor)
        self._searchResults = [] # private list used to search for nodes
        self._currentMatch = None

        self.currentParamFrame = None #node's param panel frame

    def _search(self, name, node, path=[]):
        path.append(node)
        if name in node.name:
            self._searchResults.append(path[:])
        for child in node.children:
            path = self._search(name, child, path)
        path.pop()
        return path


    def showSearchResult(self, index):
        rlen = len(self._searchResults)
        index = self._currentMatch = index%rlen
        if rlen==0: return
        path = self._searchResults[index]
        for p in path:
            item = self.tree.objToItem[p]
            self.tree.item_expand(item)
        self.tree.see(item, center='y')
        self.tree.selection_clear()
        self.tree.selection_add(item)
        #print 'SHOWING', index, item, self._searchResults[index][-1].name


    def previousMatch(self, event=None):
        self.showSearchResult( (self._currentMatch-1)%len(self._searchResults) )
        

    def nextMatch(self, event=None):
        self.showSearchResult( (self._currentMatch+1)%len(self._searchResults) )


    def search(self, event=None):
        self._searchResults = []
        searchString = self.searchStringTk.get()
        if len(searchString):
            self._search(searchString, self.rootNode)
            if len(self._searchResults)==0:
                self.upArrowTk.configure(state=Tkinter.DISABLED)
                self.downArrowTk.configure(state=Tkinter.DISABLED)
            else:
                self.upArrowTk.configure(state=Tkinter.NORMAL)
                self.downArrowTk.configure(state=Tkinter.NORMAL)
                
                self.showSearchResult(0)
            #print 'search', self.searchStringTk.get()
            #for res in self._searchResults:
            #    print [p.name for p in res],
            #    print


    def showNodeParameters(self, frame):
        self.notebook.selectpage('Parameters')
        if self.currentParamFrame:
            self.currentParamFrame.forget()
        frame.pack(fill='both', expand=1)
        self.currentParamFrame = frame

    def showNodeDoc(self):
        self.notebook.selectpage('doc')


    def createTree(self, master):
        self.family = ''
        self.FONT = tkFont.Font(family=self.family, size=9)
        self.FONTlargebold = tkFont.Font(family=self.family, size=11, weight='bold')
        self.FONTbold = tkFont.Font(family=self.family, size=9, weight="bold")

        self.master = master

        # create paned widget to hold tree on top and doc frame at bottom
        self.pane = Pmw.PanedWidget(master, orient='vertical', handlesize=0,
                                    separatorthickness=10, separatorrelief='raised', )
        top = self.pane.add('tree', min=10, size=self.treeHeight)
        notebookMaster =  self.pane.add('NoteBook', min=0, size=self.docHeight)

        # create a noteBook in the bottom pane
        self.notebook = Pmw.NoteBook(notebookMaster)
        self.paramPanelMaster = params = self.notebook.add('Parameters')
        docTab = self.notebook.add('doc')
        self.notebook.pack(expand=1, fill='both')
        
        #bottom =  self.pane.add('doc', min=0, size=self.docHeight)
        handle = self.pane.component('handle-1')
        sep = self.pane.component('separator-1')
        #self.pane.component('handle-1').place_forget()
        #self.pane.component('handle-1').forget()
        #self.pane.component('handle-1').pack_forget()
        #self.pane.component('handle-1').grid_forget()
        self.pane.component('separator-1').configure(
            bd =2, #bg = '#999999'
            highlightthickness=1, highlightbackground='black', highlightcolor='black')

        # separator for rearranging 
        spacer = Tkinter.Frame(notebookMaster, height=10)
        spacer.pack(expand=0, fill='x',side='top', anchor='n')

        # create the handle in the separator bar
        Tkinter.Frame(sep, height=4, width=40, bg='#fffeee', relief='sunken',
                      bd=1, highlightbackground='black', highlightthickness=1).pack(
            anchor='center', padx=2, pady=2, side='top', expand=0, fill=None)

        self.pane.pack(expand=1,fill='both')

        self.treeMaster= Tkinter.Frame(top)

        ## build aframe for search for nodes
        ##
        self.searchFrame = Tkinter.Frame(self.treeMaster)

        # magnifying glass icon
        filename = os.path.join(ICONPATH, 'search.png')
        self.magnifyGlassIcon = ImageTk.PhotoImage(file=filename)
        width = self.magnifyGlassIcon.width()
        height = self.magnifyGlassIcon.height()
        button = Tkinter.Button(self.searchFrame, width=width, height=height,
                                command=None, image=self.magnifyGlassIcon)
        button.pack(side='left')
        
        # search entry widget
        self.searchStringTk = Tkinter.StringVar()
        self.searchEntry = Tkinter.Entry(self.searchFrame, textvariable=self.searchStringTk,
                                         width=1)
        self.searchEntry.bind('<Return>', self.search)
        self.searchEntry.pack(side='left', fill='x', expand=1)

        # next and previous buttons
        filename = os.path.join(ICONPATH, 'arrowDown.png')
        self.downArrowIcon = ImageTk.PhotoImage(file=filename)
        width = self.magnifyGlassIcon.width()
        height = self.magnifyGlassIcon.height()
        button = self.downArrowTk = Tkinter.Button(
            self.searchFrame, width=width, height=height, state=Tkinter.DISABLED,
            command=self.nextMatch, image=self.downArrowIcon)
        button.pack(side='left')

        filename = os.path.join(ICONPATH, 'arrowUp.png')
        self.upArronIcon = ImageTk.PhotoImage(file=filename)
        width = self.magnifyGlassIcon.width()
        height = self.magnifyGlassIcon.height()
        button = self.upArrowTk = Tkinter.Button(
            self.searchFrame, width=width, height=height, state=Tkinter.DISABLED,
            command=self.previousMatch, image=self.upArronIcon)
        button.pack(side='left')

        self.searchFrame.pack(side='top', fill='x', expand=0)

        # create tree widget for libraries tree
        libView = TkTreectrl.ScrolledTreectrl(self.treeMaster, width=200, height=self.treeHeight)
        libView.pack(side='top', fill='both', expand=1)

        self.treeMaster.pack(side='top', fill='both', expand=1)
        
        fixedFont = Pmw.logicalfont('Fixed')
        self.docFrame = ScrolledFormatedText(
            docTab, label_text='Description:',
            labelpos = 'nw', usehullsize = 1, hull_height = 1500,
            )
        #self.docCanvas = Tkinter.Canvas(self.docFrame, height=150, bg='grey75')
        self.nodeInDocFrame = None
        self.docFrame.pack(side='top', fill='both', expand=0)

        self.libView = libView
        
        self.tree = tree = libView.treectrl
        self.rootNode = rootNode = Node()
        tree.itemToObj={ TkTreectrl.ROOT : rootNode }
        tree.objToItem = { rootNode : TkTreectrl.ROOT } 

        self.libTreeCol = tree.column_create(text="")
        tree.configure(treecolumn=self.libTreeCol, showbuttons=1,
                       font=self.FONT)
        #tree.column_dragconfigure(enable=1)

        # style for library node in tree
        libStyle = tree.style_create()
        el_text = tree.element_create(type=TkTreectrl.TEXT)
        el_select = tree.element_create(type=TkTreectrl.RECT, showfocus=1,
                                        fill=('orange', TkTreectrl.SELECTED))
        tree.style_elements(libStyle, el_select, el_text)
        tree.style_layout(libStyle, el_select, union=(el_text, ), ipady=1, iexpand='nsew')
        tree.style_layout(libStyle, el_text, padx=8, pady=2, squeeze='y')
        self.treeStyles['library'] = {'text' : el_text, 'style' : libStyle}

        # style for category node in tree
        categoryStyle = tree.style_create()
        el_text = tree.element_create(type=TkTreectrl.TEXT)
        el_select = tree.element_create(type=TkTreectrl.RECT, showfocus=1,
                                        fill=('pink', TkTreectrl.SELECTED))
        tree.style_elements(categoryStyle, el_select, el_text)
        tree.style_layout(categoryStyle, el_select, union=(el_text, ), ipady=1, iexpand='nsew')
        tree.style_layout(categoryStyle, el_text, padx=8, pady=2, squeeze='y')
        self.treeStyles['category'] = {'text' : el_text, 'style' : categoryStyle}

        ## # style for model nodes in tree
        ## nodeStyle = tree.style_create()

        ## el_image = tree.element_create(type=TkTreectrl.IMAGE,
        ##                                image=(self.modelTreeIcon, TkTreectrl.OPEN, self.modelTreeIcon, ''))
        ## el_text = tree.element_create(type=TkTreectrl.TEXT)
        ## el_select = tree.element_create(type=TkTreectrl.RECT, showfocus=1,
        ##                                 fill=('yellow1', TkTreectrl.SELECTED))
        ## tree.style_elements(nodeStyle, el_image, el_select, el_text)
        ## tree.style_layout(nodeStyle, el_select, union=(el_text, ), ipady=1, iexpand='nsew')
        ## tree.style_layout(nodeStyle, el_text, padx=8, pady=2, squeeze='y')
        ## tree.style_layout(nodeStyle, el_image, pady=2)
        ## self.treeStyles['model'] = {'text' : el_text, 'style' : nodeStyle, 'image':el_image,
        ##                            'text':el_text, 'select':el_select}

        ## # style for system nodes in tree
        ## nodeStyle = tree.style_create()

        ## el_image = tree.element_create(type=TkTreectrl.IMAGE,
        ##                                image=(self.systemTreeIcon, TkTreectrl.OPEN, self.systemTreeIcon, ''))
        ## el_text = tree.element_create(type=TkTreectrl.TEXT)
        ## el_select = tree.element_create(type=TkTreectrl.RECT, showfocus=1,
        ##                                 fill=('yellow1', TkTreectrl.SELECTED))
        ## tree.style_elements(nodeStyle, el_image, el_select, el_text)
        ## tree.style_layout(nodeStyle, el_select, union=(el_text, ), ipady=1, iexpand='nsew')
        ## tree.style_layout(nodeStyle, el_text, padx=8, pady=2, squeeze='y')
        ## tree.style_layout(nodeStyle, el_image, pady=2)
        ## self.treeStyles['system'] = {'text' : el_text, 'style' : nodeStyle, 'image':el_image,
        ##                              'text':el_text, 'select':el_select}

        # assign library style to root
        tree.itemstyle_set(TkTreectrl.ROOT, self.libTreeCol, libStyle)
        tree.itemelement_config(
            TkTreectrl.ROOT, self.libTreeCol, self.treeStyles['library']['text'],
            text='Libraries', font=self.FONTlargebold)

        tree.notify_bind('<Expand-before>', self.expandNode_cb)
        #tree.notify_install('<Drag-begin>')
        #tree.notify_bind('<Drag-begin>', self.dragBegin)
        #tree.notify_bind('<Scroll-x>', self.scrollX)
        #tree.notify_bind('<Scroll-y>', self.scrollY)

        tree.bind('<ButtonPress-1>', self.buttonPress1)

    #def scrollX(self, event):
    #    print 'Scroll-X', event
        
    #def scrollY(self, event):
    #    print 'Scroll-Y', event
        
    ## not called when I drag :(
    ## def dragBegin(self,event):
    ##     print 'drag'
    def where(self, canvas, event):
        # compute coordinates of event.x and event.y in canvas
        
        # where the corner of the visible canvas is relative to the screen:
        x_org = canvas.winfo_rootx()
        y_org = canvas.winfo_rooty()
        # where the pointer is relative to the canvas widget:
        x = event.x_root - x_org + canvas.canvasx(0)# - self.initialWinXoff
        y = event.y_root - y_org + canvas.canvasy(0)# - self.initialWinYoff
        # compensate for initial pointer offset
        #return x - self.x_off, y - self.y_off
        return x, y

        
    def buttonMove1(self, event=None):

        tree = event.widget
        win = tree.winfo_containing(event.x_root, event.y_root)
        if win != self.currentWin:
            if win==self.editor().currentNetwork.canvas:
                x, y = self.where(win, event)
                
                self.dndId = win.create_image(
                    x, y, image=self.nodeInDocFrame.imagetk)
                self.currentWin = win
                self.lastx = x
                self.lasty = y
                
        else:
            if isinstance(win, Tkinter.Canvas):
                x, y = self.where(win, event)
                dx = x - self.lastx
                dy = y - self.lasty
                win.move(self.dndId, dx, dy)
                self.lastx = x
                self.lasty = y
            elif win==tree:
                offx = tree.canvasx(event.x) - self._x
                offy = tree.canvasx(event.y) - self._y
                tree.dragimage_offset(offx, offy)

        #tree.xview('moveto', self._position[0])
        #tree.yview('moveto', self._position[1])


    def buttonRelease1(self, event=None):
        tree = event.widget
        win = tree.winfo_containing(event.x_root, event.y_root)
        tree.configure(xscrolldelay=50, yscrolldelay=50)
        if isinstance(win, Tkinter.Canvas):
            bbox = win.bbox(self.dndId)
            posx = bbox[0]
            posy = bbox[1]
            #win.delete(self.dndId)
            # create the real node            
            kw = self.nodeToCreate.kw
            args = self.nodeToCreate.args            
            ## # load library if not loaded
            ## loaded = False
            ## for name, lib in self.editor().libraries.items():
            ##     #print lib, kw['library'], lib.name, kw['library'].name
            ##     if lib == kw['library']:
            ##         loaded = True

            ## if not loaded:
            ##     lib = kw['library']
            ##     #print 'loading', lib, lib.modName
            ##     self.editor().addLibraryInstance(lib, lib.modName, lib.varName)

            # find node styles
            klass = self.nodeToCreate.nodeClass

            node = klass( *args, **kw )
            self.editor().currentNetwork.addNode(node, posx, posy)

        tree.unbind('<B1-Motion>')
        tree.unbind('<ButtonRelease-1>')
        tree.dragimage_configure(visible=0)
        tree.dragimage_clear()
        # delete the image used to move the node
        if self.dndId:
            self.currentWin.delete(self.dndId)
            
        # restore scrolling
        #if self.libView._scrollmode == 'auto':
        #    self.libView._scrolledWidget.configure(xscrollcommand=self.libView._scrollBothLater,
        #                                          yscrollcommand=self.libView._scrollBothLater)
        #else:
        #    self.libView._scrolledWidget.configure(xscrollcommand=self.libView._scrollXNow,
        #                                          yscrollcommand=self.libView._scrollYNow)
        tree.xview('moveto', self._position[0])
        tree.yview('moveto', self._position[1])

    def buttonPress1(self, event):
        tree = event.widget
        self.dndId = None

        # attempt to deal with tree scrolling while dragging nodes
        # self._position is use to reset tree view as we release mouse button
        # scrolldelay is attemt to prevent tree form scrolling (not reliable)
        self._position = tree.canvasx(0), tree.canvasy(0)
        tree.configure(xscrolldelay=100000, yscrolldelay=100000)

        # Clean up previous scroll commands to prevent memory leak.
        #tclCommandName = str(self.libView._scrolledWidget.cget('xscrollcommand'))
        #if tclCommandName != '':
        #    print 'COMMAND NAME X', tclCommandName
        #    self.libView._scrolledWidget.deletecommand(tclCommandName)
        #tclCommandName = str(self.libView._scrolledWidget.cget('yscrollcommand'))
        #if tclCommandName != '':
        #    print 'COMMAND NAME Y', tclCommandName
        #    self.libView._scrolledWidget.deletecommand(tclCommandName)

        #def dummyX(*args):
        #    print 'DummyX', args

        #def dummyY(*args):
        #    print 'DummyY', args

        ## disable scrolling
        #self.libView._scrolledWidget.xview = xview
        #self.libView._scrolledWidget.yview = xview
        #self.libView.vbar.configure(command = dummyX)
        #self.libView.hbar.configure(command = dummyY)
        #self.libView._scrolledWidget.configure(xscrollcommand=dummyX, yscrollcommand=dummyY)
        #self.libView.treectrl.xview = xview
        #self.libView.treectrl.xview_moveto = xview
        #self.libView.treectrl.xview_scroll = xview
        
        ## stuff for DND
        self.currentWin = tree.winfo_containing(event.x_root, event.y_root)
        self.lastx = tree.canvasx(event.x)
        self.lasty = tree.canvasy(event.y)

        identify = tree.identify(event.x, event.y)
        if identify:
            try:
                item, column, element = identify[1], identify[3], identify[5]
                #print 'AAAAAAA', item, column, element
                if int(column)==self.libTreeCol:  # click on tree
                    obj = self.tree.itemToObj.get(item, None)

                    # clear the text in the doc frame
                    text = self.docFrame
                    text.clear()

                    # delete the icon from the canvas
                    if self.nodeInDocFrame:
                        self.nodeInDocFrame.deleteIcon()
                        self.nodeInDocFrame = None
                        
                    if obj and isinstance(obj.object, NodeProxy):
                        np = obj.object
                        text.configure(label_text='Description: %s'%np.name)
                        self.nodeToCreate = np
                        n = np.nodeClass(*np.args, **np.kw)
                        
                        self.clickedNode = n
                        n.setEditor(self.editor())

                        for kw in n.outputPortsDescr:
                            kw['updateSignature'] = False
                            op = n.addOutputPort( **kw )

                        for kw in n.inputPortsDescr:
                            kw['updateSignature'] = False
                            ip = n.addInputPort( **kw )
                        canvas = self.editor().currentNetwork.canvas
                        n.buildNodeIcon(canvas, -2000, -2000)
                        self.nodeInDocFrame = n
                        # build an image in the tree for DnD
                        tree.dragimage_add(item)
                        tree.dragimage_configure(visible=1)
                        self._x = tree.canvasx(event.x)
                        self._y = tree.canvasy(event.y)
                        #tree.marquee_coords(*tree.item_bbox(item))
                        #tree.marquee_configure(visible=1)
                        #print 'AAA', tree.marquee_coords()
                        #print 'AAA', tree.dragimage_configure()
                        #print 'BBB', tree.dragimage_offset()
                        #tree.dragimage_offset(50, 50)
                        #self.dndImageTk = tree.tk.call(tree._w, 'create', 'image',
                        #                               -2000, -2000, n.imagetk)
                        
                        textw = text.component('text')
                        textw.image_create('end', image=n.imagetkRot, align='center')
                        text.renderText(n.__doc__)

                        tree.bind('<B1-Motion>', self.buttonMove1)
                        tree.bind('<ButtonRelease-1>', self.buttonRelease1)

            except IndexError:
                # we did not hit the image, never mind
                pass


    def expandNode_cb(self, event):
        item = event.item
        obj = self.tree.itemToObj.get(item, None)
        #print "EXPAND NODE_CB", obj.name
        self.expandNode(obj)


    def expandNode(self, obj):
        item = self.tree.objToItem.get(obj, None)
        #print 'EXPAND', obj.name, item, obj, len(obj.children)

        if len(obj.children):
            #print 'adding button to ', obj.name
            self.tree.item_config(item, button=True)

        if obj==self.rootNode:
            style = self.treeStyles['library']['style']
            text = self.treeStyles['library']['text']
        elif isinstance(obj.object, NodeLibrary):
            style = self.treeStyles['category']['style']
            text = self.treeStyles['category']['text']
        elif isinstance(obj.object, dict): # models and systems
            text = self.treeStyles['category']['text']
            style = self.treeStyles['category']['style']
            
        for child in obj.children:
            button = len(child.children)>0
            if self.tree.objToItem.has_key(child):
                citem = self.tree.objToItem[child]
                self.tree.item_config(citem, button=button)
            else:
                new = self.tree.create_item(
                    parent=item, button=button, open=0)[0]
                # create bi-directional lookup
                self.tree.itemToObj[new] = child
                self.tree.objToItem[child] = new
                ## try:
                ##     if child.object.libTreeIcon=='system':
                ##         style = self.treeStyles['system']['style']
                ##     elif child.object.libTreeIcon=='model':
                ##         style = self.treeStyles['model']['style']
                ##     print child.object.libTreeIcon, style
                ## except AttributeError:
                ##     pass
                self.tree.itemstyle_set(new, self.libTreeCol, style)
                self.tree.itemelement_config(
                    new, self.libTreeCol, text, text=child.name,
                    font=self.FONT)
                #print child.object, hasattr(child.object, 'libTreeIcon')
                #if hasattr(child.object, 'libTreeIcon'):
                #    self.tree.itemelement_config(
                #        new, self.libTreeCol, self.treeStyles['model']['image'],
                #        image=child.object.libTreeIcon)


    def addLibrary(self, lib):
        ##
        ## add a library
        ## categories can use . to create subcategories
        if len(lib.version):
            name = '%s %s'%(lib.name, lib.version)
        else:
            name = lib.name
        root = node = Node(name, lib)
        self.rootNode.addChild(node) # node for library

        catList = lib.libraryDescr.keys()
        catList.sort()
        parentNodes = {} # keep track of parent nodes {'category':Node}
        for cat in catList:
            parent = root
            path = cat.split('.')
            currentPath = ''
            d = lib.libraryDescr[cat]

            for catname in path: # find nodes for category path or create them
                currentPath += '.'+catname
                try:
                    catnode = parentNodes[currentPath]
                except KeyError:
                    catnode = Node(catname, d)  # node for category
                    parent.addChild(catnode)
                    parentNodes[currentPath] = catnode
                parent = catnode

            # add the nodes in that (sub)category
            nodesByName = {}
            for n in d['nodes']: 
                nodesByName[n.name] = n
            nodeNames = nodesByName.keys()
            nodeNames.sort()
            for vnodeName in nodeNames:
                vnode = nodesByName[vnodeName]
                tvnode = Node(vnode.name, vnode)
                catnode.addChild(tvnode)
                
        self.tree.notify_generate('<Expand-before>', item=TkTreectrl.ROOT)
        return node
    

if __name__=='__main__':
    #root = Tkinter.Tk()
    root = WarpIV.ed.libtreeMaster
    tree = LibTree(root)
    
    #from Vision.StandardNodes import stdlib
    from MissileDefenseDemo_v0_1 import MissileDefenseDemo
    tree.addLibrary(MissileDefenseDemo)
    
    #execfile('libTree.py')
