import TkTreectrl, ImageTk, os, Tkinter, weakref
import tkFont

import sys
# Research
#   '- Projects ( "HIV", "HDAC-2", ....)
#        '- Experiment ( "protease fragments", "integrase_various", )
#             '- VirtualScreening ( "recname_libname" )

class Node:
    """
    Base class for a hierarchy of nodes
    """
    def __init__(self, name, childKlass):
        self.name = name
        self.parent = None
        self.childKlass = childKlass
        self.children = []


    def addChild(self, child):
        """
        """
        assert isinstance(child, self.childKlass), "Expecred %s instance, got %s" %(
            self.childKlass, child.__class__)
        self.children.append(child)
        child.parent = weakref.ref(self)


    def getChild(self, name):
        """
        """
        for child in self.children:
            if child.name==name: return child
        return None


    def delete(self):
        """
        """
        for c in self.children:
            c.delete()
        self.parent().children.remove(self)
        self.parent = None
        

    def traverseByType(self, ntype, results):
        """
        """
        if isinstance(self, ntype):
            return [self]
        for c in self.children:
            if isinstance(c, ntype):
                results.append(c)
            else:
                c.traverseByType(ntype, results)
        return results
    


class Research(Node):
    """
    """
    def __init__(self, name='NoName'):
        Node.__init__(self, name, Project)
        self.properties = {}


class Project(Node):

    def __init__(self, name):
        Node.__init__(self, name, Experiment)
        self.properties = {}


class Experiment(Node):
    """
    """
    def __init__(self, name):
        Node.__init__(self, name, VirtualScreening)
        self.properties = {}
        self.status = ''



class VirtualScreening(Node):
    """
    """
    def __init__(self, name, date, url, status, jobId, resurl): 
        """
        """
        Node.__init__(self, name, None)
        self.date = date
        self.properties = { 'job_type' : 'opal', # linux_cluster, local
                            'lig_library' : 'NCIdiv2',
                            'submission_date': '1/1/1970',
                            'results_location': '',
                            'receptor' : '',
                          }

        # OPAL service
        self.url = url
        self.status = status
        self.jobId = jobId
        self.resurl = resurl
        if resurl:
            self.properties['results_location'] = resurl

    def kill(self):
        import OpalClient
        server = OpalClient.OpalService(self.url)
        checker = OpalClient.JobStatus(server, self.jobId)
        if checker.isRunning():
            checker.destroyJob()
            self.status = 'Killed/Error'


    def getresurl(self):
        import OpalClient
        server = OpalClient.OpalService(self.url)
        checker = OpalClient.JobStatus(server, self.jobId)
        try:
            resurl = os.path.dirname(checker.getOutputFiles()[0])
        except:
            resurl  = '[ expired data? ]'
            #print "getresurl error", sys.exc_info()[1]
        return resurl
            
    def downloadres(self, path):
        import OpalClient
        server = OpalClient.OpalService(self.url)
        checker = OpalClient.JobStatus(server, self.jobId)
        try:
            checker.downloadOutput(path)
            return True
        except:
            return False

    def getfullname(self):
        """ return vs fullname  = [ prj_name, exp_name, vs_name ]"""
        #exp_name = self.parent.name
        #prj_name = self.parent.parent.name
        return [ self.parent().parent().name, self.parent().name, self.name ]
        


# project
#    virtual_screenings 
#       rec_vs ( rec + lig_lib )


class VSresultsTree:

    def __init__(self, root, fname=None, iconpath = None):

        import Pmw, Tkinter
        import TkTreectrl, ImageTk
        import os
        import tkFont
        import OpalClient
        #ICONPATH='icons/'
        family = 'Bitstream vera sans'
        #family = 'Arial'
        self.FONT = tkFont.Font(family=family,size=9)
        self.FONTlargebold = tkFont.Font(family=family,size=11, weight='bold')
        self.FONTbold = tkFont.Font(family=family,size=9,weight="bold")
        from CADD.Raccoon import ICONPATH
        
        self._iconpath=ICONPATH
        # print "UICONPATH", self._iconpath

        Tkinter.wantobjects=0
        self.root = root

        self._initTree()

        if fname:
            self.setDataFile(fname)
            #self._populateItems(fname)

            #self._activateTree()


    def traverse(self, node):
    
        if len(node.children)==0: # node is job
            #print 'JOB', node.name
            #query status and update tree for job
            return 'Succeess'

        results = []
        for child in node.children:
            results.append(self.traverse(child))

        ## all children of node have been visited
        #if isinstance(node, Experiment):
            #print 'VS', node.name, results
            # update VS status using results
        return results


##     def traverseByType(self, node, ntype = None, results = [] ):
##         """ traverse the graph returning all objects matching ntype """
##         if ntype == None:
##             return
##         if len(node.children) == 0:
##             return []

##         if isinstance(node, ntype):
##             if not node in results:
##                 results.append(node)

##         for child in node.children:
##             if isinstance(child, ntype):
##                 if not child in results:
##                     results.append(child)
##             self.traverseByType(child, ntype = ntype, results = results)
##         return results

    def findVsParent(self, vs):
        """ return the parent Experiment of the VS """
        prj_list = []
        self.traverseByType( self.research, ntype = Experiment, 
            results = prj_list)
        for p in prj_list:
            if vs in p.children:
                return p
        return None


    def buildGraph(self, node, useName=True):
        # NOTE store c.name or c as obj?
        results = {}
        if hasattr(node, 'children'):
            for c in node.children:
                if useName:
                    key = c.name
                else:
                    key = c
                results[key] = self.buildGraph(self.buildGraph(c), useName=useName)
        else:
            return node
        return results

    def getTreeGraph(self, useName=True):
        return self.buildGraph(self.research, useName=useName)


    def setDataFile(self, fname):
        self._populateItems(fname)
        self._activateTree()

    def _activateTree(self):
        self._buildTree()
        self.tree.notify_generate('<Expand-before>', item=TkTreectrl.ROOT)
        self.tree.see(TkTreectrl.ROOT)


    def _populateItems(self, fname):

        f = open(fname)
        data = f.readlines()
        f.close()

        try:
            projects ={}
            for line in data:
                word = [w.strip()[1:-1] for w in line.split('\t')]
                project = word[0]
                experiment = word[1]
                receptor = word[2]
                date = word[3]
                url = word[4]
                status = word[5]
                jobId = word[6]
                resurl = word[7]
                try:
                    reslocation = word[8]
                except:
                    reslocation = "" 
                # XXX PROBABLY OBSOLETE
                try:
                    hidden = words[9]
                except:
                    hidden = ''

                proj = projects.get(project, None)
                if proj is None:
                    pro = Project(project)
                    self.research.addChild(pro)
                    exp = Experiment(experiment)
                    pro.addChild(exp)
                    projects[project] = pro
                else:
                    pro = projects[project]
                    exp = pro.getChild(experiment)
                    if exp is None:
                        exp = Experiment(experiment)
                        pro.addChild(exp)
                        
                job = VirtualScreening( receptor, date, url, status, jobId, resurl)
                job.properties['results_location'] = reslocation
                exp.addChild(job)
        except:
            print "ERROR: PrjManagerTree|_populateItems> possible old version file format for history (missing columns?)"
            return
    
    

    def _initTree(self):
        #print "INIT TREE"
        self.treeObj = TkTreectrl.ScrolledTreectrl(self.root)
        self.treeObj.pack(expand=1,fill='both')
        self.tree = self.treeObj.treectrl

        self.research = Research()
        self.tree.itemToObj={ TkTreectrl.ROOT : self.research } # gives obj from tree items
        self.tree.objToItem = {self.research : TkTreectrl.ROOT} # give tree items from obj



    def _buildTree(self):

        self.tree.columns = []
        #jobname_col= self.tree.column_create(text="jobname")
        jobname_col= self.tree.column_create(text="")
        self.tree.columns.append(jobname_col)
        self.tree.configure(treecolumn=jobname_col, showbuttons=1, font=self.FONT)
        self.tree.columns.append(self.tree.column_create(text='status', expand=1))
        self.tree.columns.append(self.tree.column_create(text='date', expand=1))
        self.tree.columns.append(self.tree.column_create(text='service URL', expand=0))
        self.tree.columns.append(self.tree.column_create(text='jobId', expand=0))
        self.tree.columns.append(self.tree.column_create(text='results URL', expand=0))

        #checkedIcon = self.tree.icons['checkedIcon'] = \
        #            Tkinter.PhotoImage(master=master, data='R0lGODlhDQANABEAACwAAAAADQANAIEAAAB/f3/f39////8CJ4yPNgHtLxYYtNbIbJ146jZ0gzeCIuhQ53NJVNpmryZqsYDnemT3BQA7')
        self._molIcon = molIcon = ImageTk.PhotoImage(
                    file=os.path.join(self._iconpath, 'water2.png'))
        self._cogIcon = cogIcon = ImageTk.PhotoImage(
                    file=os.path.join(self._iconpath, 'system.png'))

        self._jobIcon = jobIcon =  ImageTk.PhotoImage(
                    file=os.path.join(self._iconpath, 'basket.png'))

        self._treeStyles = {}

        # text style

        # style for project
        styleProject = self.tree.style_create()
        pel_image = self.tree.element_create(type=TkTreectrl.IMAGE,
                                    image=(molIcon, TkTreectrl.OPEN, molIcon, ''))

        pel_text = self.tree.element_create(type=TkTreectrl.TEXT,  fill=('white', TkTreectrl.SELECTED))
        pel_select = self.tree.element_create(type=TkTreectrl.RECT, showfocus=1,
                                     fill=('blue4', TkTreectrl.SELECTED))
        self.tree.style_elements(styleProject, pel_image, pel_select, pel_text)
        self.tree.style_layout(styleProject, pel_image, pady=1)
        self.tree.style_layout(styleProject, pel_select, union=(pel_text,), padx=1, pady=1, squeeze='')
        self.tree.style_layout(styleProject, pel_text, padx=1, pady=1, ipadx=2,ipady=2) #, squeeze='y')
        self.tree.itemstyle_set(TkTreectrl.ROOT, jobname_col, styleProject)
        self.tree.itemelement_config(TkTreectrl.ROOT, jobname_col, pel_text, text='Raccoon jobs',
                                    font =self.FONTlargebold)
                                     #datatype=TkTreectrl.STRING, data='top')
        self._treeStyles['prj'] = { 'img' : pel_image, 'txt' : pel_text, 'style' : styleProject}



        # style for jobs
        styleJob = self.tree.style_create()
        job_image = self.tree.element_create(type=TkTreectrl.IMAGE,
                                    image=(jobIcon, TkTreectrl.OPEN, jobIcon, ''))
        #pel_text = self.tree.element_create(type=TkTreectrl.TEXT,  fill=('white', TkTreectrl.SELECTED))
        self.tree.style_elements(styleJob, job_image, pel_select, pel_text)
        self.tree.style_layout(styleJob, pel_select, union=(pel_text,), padx=1, pady=1, ipadx=1,ipady=1 ) #, squeeze='y')
        self.tree.style_layout(styleJob, job_image, pady=2)
        self._treeStyles['job'] = { 'img' : job_image, 'txt' : pel_text, 'style' : styleJob}




        # style for string cell
        styleString = self.tree.style_create()
        cel_text = self.tree.element_create(type=TkTreectrl.TEXT,  fill=('white', TkTreectrl.SELECTED))
        #el_text = self.tree.element_create(type=TkTreectrl.TEXT)
        #cel_image = self.tree.element_create(type=TkTreectrl.IMAGE,
        #                            image=(molIcon, TkTreectrl.OPEN, molIcon, ''))
        #el_select1 = self.tree.element_create(type=TkTreectrl.RECT, showfocus=1,
        #                             fill=('blue4', TkTreectrl.SELECTED))
        self.tree.style_elements(styleString, pel_select, cel_text)
        self.tree.style_layout(styleString, cel_text, padx=1, pady=1, squeeze='y')
        self.tree.style_layout(styleString, pel_select, union=(cel_text,), padx=1, pady=1, ipadx=1,ipady=1 )
        #self.tree.itemstyle_set(TkTreectrl.ROOT, jobname_col, styleProject)

        self._treeStyles['cell'] = { 'txt' : cel_text, 'style' : styleString}



    


        


        # bindings
        self.tree.notify_bind('<Expand-before>', self.expandNode_cb)

        #self.tree.bind('<Double-Button-1>', self.on_button1)
        #self.tree.bind('<ButtonRelease-3>', self.on_button3)
                

    def expandNode_cb(self, event):
        #print "prj EXAPAND NODECB"
        item = event.item
        obj = self.tree.itemToObj.get(item, None)
        self.expandNode(obj)
            


    def expandNode(self, obj):
        item = self.tree.objToItem.get(obj, None)
        if item is None:
            raise RuntimeError ('expanding node without item')
    
        if self.tree.item_numchildren(item)==len(obj.children):
            #print "ITEMCHILD", self.tree.item_numchildren(item)
            # directory has already been drawn, don't bother to track changes to the directory structure here
            #print 'RETURN because already expanded'
            return

        if len(obj.children):
            self.tree.item_config(item, button=True)

        prj  = self._treeStyles['prj']
        cell = self._treeStyles['cell']
        job  = self._treeStyles['job']

        p_txt = prj['txt']
        p_img = prj['img']
        p_style = prj['style']
        c_txt = cell['txt']
        c_style = cell['style']

        # that's a trick: store the item's full path in the text element's data option
        #data = self.tree.itemelement_cget(item, self.tree.columns[0], p_txt , 'data')

        #print "data:", data
        #print 'obj :', obj
        
        #print "el_TEXT", p_txt
        for child in obj.children:
            if self.tree.objToItem.has_key(child):
                #print 'SKIPPING', child.name
                continue
            #print "==> child:", child.name, child
            button = len(child.children) > 0
            #print "CHILDREN", len(child.children)
            new = self.tree.create_item(parent=item, button=button, open=0)[0]
            # create bi-directional lookup
            self.tree.itemToObj[new] = child
            self.tree.objToItem[child] = new 
            #self.tree.itemstyle_set(new, self.tree.columns[0], styleProject)
            self.tree.itemstyle_set(new, self.tree.columns[0], p_style)
            self.tree.itemelement_config(new, self.tree.columns[0], p_txt, text=child.name, font=self.FONTbold)
            if isinstance(child, Experiment):
                #print "VS", child

                self.tree.itemstyle_set(new, self.tree.columns[1], c_style)
                nbSuccess = nbFail = nbRunning = 0
                for c in child.children:
                    "CSTATUS", c.status
                    if c.status=='Successful': nbSuccess +=1
                    elif c.status=='Fail': nbnbFail +=1
                    elif c.status=='Running': nbRunning +=1
                if nbSuccess==len(child.children) and nbSuccess > 0:
                    status = 'Successful'
                    status = 'SUCCESSFUL'
                    color = '#33bb33'
                elif nbFail==len(child.children) and nbFail > 0:
                    status = 'FAIL'
                    color = 'red'
                elif nbRunning == len(child.children) and nbRunning > 0:
                    status = 'RUNNING'
                    color = 'orange'
                else:
                    status = 'PARTIAL'
                    color = 'orange'
                color = 'black'
                child.status = status
                self.tree.itemelement_config(new, self.tree.columns[1], c_txt, text=status, fill=(color,),font=self.FONTbold)

            elif isinstance(child, VirtualScreening):
                style = job['style']
                text = job['txt']
                img = job['img']
                #self._treeStyles['job'] = { 'img' : job_image, 'txt' : pel_text, 'style' : styleJob}
                #print child
                self.tree.itemstyle_set(new, self.tree.columns[0], style)
                self.tree.itemelement_config(new, self.tree.columns[0], text, text=child.name, fill=('black',), font=self.FONT)
                text = cell['txt']
                style = cell['style']
                self.tree.itemstyle_set(new, self.tree.columns[1], style)
                self.tree.itemelement_config(new, self.tree.columns[1], text, text=child.status, fill=('black',), font =self.FONT )
                self.tree.itemstyle_set(new, self.tree.columns[2], style)
                self.tree.itemelement_config(new, self.tree.columns[2], text, text=child.date, fill=('black',), font=self.FONT)
                self.tree.itemstyle_set(new, self.tree.columns[3], style)
                self.tree.itemelement_config(new, self.tree.columns[3], text, text=child.url, fill=('black',), font=self.FONT)
                self.tree.itemstyle_set(new, self.tree.columns[4], style)
                self.tree.itemelement_config(new, self.tree.columns[4], text, text=child.jobId, fill=('black',), font=self.FONT)
                self.tree.itemstyle_set(new, self.tree.columns[5], style)
                self.tree.itemelement_config(new, self.tree.columns[5], text, text=child.resurl, fill=('black',), font=self.FONT)


if __name__ == '__main__':
    import Pmw, Tkinter
    import TkTreectrl, ImageTk
    import os
    ICONPATH='.'
    print "START"
    fname = '/entropia/.mgltools/latest/Raccoon/raccoon_opal.hist'
    fname = 'raccoon_opal.hist'
    fname ='null'
    root = Tkinter.Tk()
    vst = VSresultsTree(root, fname)
