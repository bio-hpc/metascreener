
import TkTreectrl, ImageTk, os, Tkinter, weakref
#from ImageTk import PhotoImage
import tkFont
from raccoonGUI_PrjManagerTree import Node, Research, Project, Experiment, VirtualScreening




class ResultsTree:
    """ build a tree based on the filesystem structure
        project/exp/vs

        provides a mechanism for selection of items
    """

    def __init__(self, parent, path, name = None):

        self.parent = parent
        self.path = path
        self._cosmeticInit()
        self._initTree()
        self.buildTreeGraph()
        self.name = name
        Tkinter.wantobjects=0


        
    def _cosmeticInit(self):
        #self._iconpath="icons/"
        from CADD.Raccoon import ICONPATH
        from CADD.Raccoon import RESULTFILE
        self.RESULTFILE = RESULTFILE
        self._iconpath = ICONPATH

        family = 'Bitstream vera sans'
        family = 'Arial'

        helvisB=tkFont.Font(family=family,size=9,weight="bold")
        helvis=tkFont.Font(family=family,size=9)
        #helvis=tkFont.Font(family="Helvetica",size=9)
        helvis_underline=tkFont.Font(family=family,size=9, underline=1)
        small_font=tkFont.Font(family=family,size=8)
        helvisB10=tkFont.Font(family=family,size=10,weight='bold')
        #courier=tkFont.Font(family='Courier', size = courier_size)

        self.FONTbold=helvisB
        self.FONT=helvis
        self.FONTmini = tkFont.Font(family=family,size=8)
        self.FONTnano = tkFont.Font(family=family,size=1)
        self.FONTmed = tkFont.Font(family=family,size=10, weight='bold')
        self.FONTboldTitle=helvisB10
        self.FONTsmall = small_font
        self.FONTunderline = helvis_underline



        

    def _initTree(self):
        #print "INIT TREE"
        self.treeObj = TkTreectrl.ScrolledTreectrl(self.parent)
        self.treeObj.pack(expand=1,fill='both', padx=5,pady=3)
        self.tree = self.treeObj.treectrl

        self.itemToVs = {}
        # checkbox 
        self.tree.state_define('Checked')
        
        self._checkedIcon = check = \
            Tkinter.PhotoImage(master=self.parent,
            data=('R0lGODlhDQANABEAACwAAAAADQANAIEAAAB/f3/f39',
                   '////8CJ4yPNgHtLxYYtNbIbJ146jZ0gzeCIuhQ53N',
                   'JVNpmryZqsYDnemT3BQA7'))
        self._unCheckedIcon = uncheck = \
            Tkinter.PhotoImage(master=self.parent,
            data=('R0lGODlhDQANABEAACwAAAAADQANAI',
            'EAAAB/f3/f39////8CIYyPNgHtLxYYtNbIrMZTX+l9WThwZAmSppqGmADHcnRaBQA7'))

        el_image = self.tree.element_create(type='image', image=(
            check, 'Checked', uncheck, ()))
        self.checkboxStyle = styleCheckbox = self.tree.style_create()
        self.tree.style_elements(styleCheckbox, el_image)

        self.tree.style_layout(styleCheckbox, el_image, padx=9, pady=2)

        self.research = Research()
        self.tree.itemToObj={ TkTreectrl.ROOT : self.research } # gives obj from tree items
        self.tree.objToItem = {self.research : TkTreectrl.ROOT} # give tree items from obj

        self.tree.columns = []
        firstcol = self.tree.column_create(text='Results in path')
        self.tree.columns.append(firstcol)
        self.tree.configure(treecolumn=firstcol, showbuttons=1, font=self.FONT)
        self.tree.columns.append(self.tree.column_create(text='Selected', expand=1))

        self._molIcon = molIcon = ImageTk.PhotoImage( file=os.path.join(self._iconpath, 'water2.png'))
        self._treeStyles = {}

        # project/exp style
        prj_style = self.tree.style_create()
        p_image = self.tree.element_create(type=TkTreectrl.IMAGE,
                                    image=(molIcon, TkTreectrl.OPEN, molIcon, ''))
        p_text = self.tree.element_create(type=TkTreectrl.TEXT,  fill=('white', TkTreectrl.SELECTED))
        p_select = self.tree.element_create(type=TkTreectrl.RECT, showfocus=1,
                                     fill=('blue4', TkTreectrl.SELECTED))
                
        self.tree.style_elements(prj_style, p_image, p_select, p_text)
        self.tree.style_layout(prj_style, p_image, pady=1)
        self.tree.style_layout(prj_style, p_select, union=(p_text,), padx=1, pady=1, squeeze='')
        self.tree.style_layout(prj_style, p_text, padx=1, pady=1, ipadx=2,ipady=2) #, squeeze='y')
        self.tree.itemstyle_set(TkTreectrl.ROOT, self.tree.columns[0], prj_style)
        
        self._treeStyles['prj'] = { 'img' : p_image, 'txt' : p_text, 'style' : prj_style}

        # style for jobs
        job_style = self.tree.style_create()
        job_image = self.tree.element_create(type=TkTreectrl.IMAGE,
                                    image=(molIcon, TkTreectrl.OPEN, molIcon, ''))
        self.tree.style_elements(job_style, job_image, p_select)
        self.tree.style_layout(job_style, job_image, pady=2)
        self.tree.style_layout(job_style, p_select, union=(job_image,), padx=1, pady=1, ipadx=1,ipady=1 ) #, squeeze='y')
        self._treeStyles['job'] = { 'img' : job_image, 'style' : job_style}

        
        # style for string cell
        styleString = self.tree.style_create()
        cel_text = self.tree.element_create(type=TkTreectrl.TEXT,  fill=('white', TkTreectrl.SELECTED))
        self.tree.style_elements(styleString, p_select, cel_text)
        self.tree.style_layout(styleString, cel_text, padx=1, pady=1, squeeze='y')
        self.tree.style_layout(styleString, p_select, union=(cel_text,), padx=1, pady=1, ipadx=1,ipady=1 )
        self._treeStyles['cell'] = { 'txt' : cel_text, 'style' : styleString}


        # bindings
        self.tree.notify_bind('<Expand-before>', self.expandNode_cb)
        self.tree.bind('<1>', self.on_button1)


    def expandNode_cb(self, event):
        #print "CALLED EXPANDNODE", event, event.item
        item = event.item
        obj = self.tree.itemToObj.get(item, None)
        item = self.tree.objToItem.get(obj, None)
        if item is None:
            raise RuntimeError ('expanding node without item')
    
        if self.tree.item_numchildren(item)==len(obj.children):
            # directory has already been drawn, don't bother to track changes to the directory structure here
            return

        if len(obj.children):
            self.tree.item_config(item, button=True)

        prj = self._treeStyles['prj']
        p_txt = prj['txt']
        p_style = prj['style']

        for child in obj.children:
            if self.tree.objToItem.has_key(child):
                continue
            button = len(child.children) > 0
            new = self.tree.create_item(parent=item, button=button, open=0)[0]
            # create bi-directional lookup
            self.tree.itemToObj[new] = child
            self.tree.objToItem[child] = new 
            self.tree.itemstyle_set(new, self.tree.columns[0], p_style)
            self.tree.itemstyle_set(new, self.tree.columns[1], self.checkboxStyle)
            self.tree.itemelement_config(new, self.tree.columns[0], p_txt, text=child.name, font=self.FONTbold)

            t =  self.tree
            # copy state from parent
            state = t.itemstate_forcolumn(item, t.columns[1])
            if state is not None:
                t.itemstate_forcolumn(new, t.columns[1], state)
                if isinstance(obj, VirtualScreening):
                    self.itemToObj[new] = child

    def on_button1(self, event):
        t = event.widget
        identify = t.identify(event.x, event.y)
        
        if identify:
            try:
                item, column, element = identify[1], identify[3], identify[5]
                if int(column)==1: # The value column was pressed

                    ## handle button click on check buttons in columns 1 (i.e. values)
   
                    t.itemstate_forcolumn(item, column, '~Checked')
                    state = t.itemstate_forcolumn(item, t.columns[1])
                    obj = t.itemToObj[item]
                    self.propagateCheckButtonDown( t, obj, state)
                    if state == None: # if uncheck, uncheck all ancestors
                        for parent in t.item_ancestors(item):
                            t.itemstate_forcolumn(parent, 1, '!Checked')
                            if t.item_ancestors(parent):
                                t.itemToObj[parent].selected = False
                    else:
                        for parent in t.item_ancestors(item):
                            if t.item_ancestors(parent):
                                t.itemToObj[parent].selected = True
                    

                    #if state is not None:
                    #    t.itemstate_forcolumn(new, t.columns[1], state)
                    return 'break'
            except IndexError:
                pass
 
    def propagateCheckButtonDown(self, tree, obj, state):
        # go down the tree and check all buttons
        for child in obj.children:
            item = tree.objToItem.get(child, None)
            if state == None:
                if item:    
                    tree.itemstate_forcolumn(item, 1, '!Checked')
                child.selected = False

            else:
                if item:
                    tree.itemstate_forcolumn(item, 1, 'Checked')
                child.selected = True
                
            self.propagateCheckButtonDown(tree, child, state)





    def buildTreeGraph(self, logname = ''):
        """walk the path and build prj/exp/vs structure

            a dirtree is accepted if the log file is
            found in it
        """
        def _getdir(path):
            dirlist = []
            for d in os.listdir(path):
                dfull = os.path.join(path,d)
                if os.path.isdir(dfull):
                    dirlist.append(dfull)
            return dirlist
            #return  [ d for d in os.listdir(path) if os.path.isdir(os.path.join(path,d)) ]

        if logname == '':
            logname = self.RESULTFILE

        prj_list = _getdir(self.path)
        for p in prj_list:
            exp_list = _getdir(p)
            for e in exp_list:
                vs_list = _getdir(e)
                for v in vs_list:
                    if os.path.isfile(os.path.join(v, logname)):
                        # project
                        pname = os.path.basename(p)
                        prj_obj = self.research.getChild(pname)
                        if not prj_obj:
                            prj_obj = Project(pname)
                            prj_obj.selected = False
                            self.research.addChild(prj_obj)
                        # experiment
                        ename = os.path.basename(e)
                        exp_obj = prj_obj.getChild(ename)
                        if not exp_obj:
                            exp_obj = Experiment(ename)
                            exp_obj.selected = False
                            prj_obj.addChild(exp_obj)
                        # vs
                        vname = os.path.basename(v)
                        vs_obj = VirtualScreening(vname, os.path.getmtime(v), None, None, None,None)
                        vs_obj.path = os.path.join( self.path, p, e, vname )
                        vs_obj.selected = False
                        exp_obj.addChild(vs_obj)
        self.status = len(self.research.children) > 0


        
        



