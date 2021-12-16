#       
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli
#          Molecular Graphics Lab
#  
#     The Scripps Research Institute 
#           _  
#          (,)  T  h e
#         _/
#        (.)    S  c r i p p s
#          \_
#          (,)  R  e s e a r c h
#         ./  
#        ( )    I  n s t i t u t e
#         '
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import TkTreectrl, os, Tkinter, weakref, Pmw
import tkMessageBox as tmb
import tkFileDialog as tfd
import tkFont
import CADD.Raccoon2.HelperFunctionsN3P as hf
import RaccoonBasics as rb
import RaccoonEvents
import DebugTools
import CADD.Raccoon2
import EE_jobmanager# import JobSubmissionInterface
                          #JobSubmissionInterface
import EF_resultprocessor
from mglutil.util.callback import CallbackFunction
import shutil, time
import Tkinter as tk
from PIL import Image, ImageTk
import sys
from operator import itemgetter
# Research
#   '- Projects ( "HIV", "HDAC-2", ....)
#        '- Experiment ( "protease fragments", "integrase_various", )
#             '- VirtualScreening ( "recname_libname" )
#           

class Node:
    """
    Base class for a hierarchy of nodes
    """
    def __init__(self, name, app, childKlass):
        self.name = name
        self.parent = None
        self.childKlass = childKlass
        self.children = []
        self.app = app

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
    def __init__(self, app):
        Node.__init__(self, '', app, Project)
        self.properties = {}

    def getItem(self, prj, exp, job):
        """ finds a job by prj/ex/job names"""
        for p in self.children:
            if p.name == prj:
                for e in p.children:
                    if e.name == exp:
                        for j in e.children:
                            if j.name == job:
                                return j
        return None

                
    def getPrj(self, prj):
        """ find a project by name"""
        for p in self.children:
            if p.name == prj:
                return p
        return None
                



class Project(Node):

    def __init__(self, name, app):
        Node.__init__(self, name, app, Experiment)
        self.properties = {}
                
    def getExp(self, exp):
        """ find a exp by name"""
        for e in self.children:
            if e.name == exp:
                return e
        return None
                



class Experiment(Node):
    """
    """
    def __init__(self, name, app):
        Node.__init__(self, name, app, VirtualScreening)
        self.status = ''

    def getVs(self, vs):
        """ find a vs by name"""
        for v in self.children:
            if v.name == vs:
                return v
        return None
                


class VirtualScreening(Node):
    """
    """
    def __init__(self, name, app, properties={}): # , date=None, status=None, jobId=None, storagepath=None):

        Node.__init__(self, name, app, None)
        self.properties = properties
        self.status = properties['status']
        self.date = properties['date']
        self.resource = properties['resource']


    def getfullname(self):
        """ return vs fullname  = [ prj_name, exp_name, vs_name ]"""
        return [ self.parent().parent().name, self.parent().name, self.name ]

    def deletelocalres(self):
        """ delete local copies of the results"""
        #datadir = self.app.getDataDir()
        self.app.setBusy()
        datadir = self.app.getDockingDir()
        destpath = datadir + os.sep + self.name
        shutil.rmtree(destpath)
        self.app.setReady()

    def kill(self):
        """ the kill method must be implemented by each subclass"""
        raise RuntimeError, "Kill method not implemented in for %s" % self.__class__

    def getstatus(self):
        """ the getresults method must be implemented by each subclass"""
        raise RuntimeError, "getresults method not implemented in for %s" % self.__class__

    def getresults(self):
        """ the fetchresult method must be implemented by each subclass"""
        raise RuntimeError, "fetchresults method not implemented in for %s" % self.__class__

    def deleteresults(self):
        """ the deleteresults method must be implemented by each subclass"""
        raise RuntimeError, "deleteresults method not implemented in for %s" % self.__class__



class VirtualScreeningOpal(VirtualScreening):
    """
    """
    def __init__(self, name, app, properties):
        """
        """
        VirtualScreening.__init__(self, name, app, properties)
        # OPAL service
        #self.url = url
        #self.resurl = resurl
        #if resurl:
        #    self.properties['results_location'] = resurl

    def kill(self):
        #import OpalClient
        server = OpalClient.OpalService(self.url)
        checker = OpalClient.JobStatus(server, self.jobId)
        if checker.isRunning():
            checker.destroyJob()
            self.status = 'Killed/Error'

    """
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
    """
            
    def getresults(self):
        import OpalClient
        server = OpalClient.OpalService(self.url)
        checker = OpalClient.JobStatus(server, self.jobId)
        try:
            checker.downloadOutput(self.storagepath)
            return True
        except:
            return False
        
    def getstatus(self):
        """ """
        return False


class VirtualScreeningSsh(VirtualScreening):
    """
    """
    def __init__(self, name, app, properties={}): #date=None, status=None, jobId=None, host=None):
        """
        """
        VirtualScreening.__init__(self, name=name, app=app, properties=properties)


    def getserver(self):
        """ """
        # XXX unclear function
        return self.parent.getserver()


    def kill(self):
        """ ask the server to use the scheduler to kill the job"""
        self.app.server.killJob(self.name)

    def getstatus(self):
        """ update the job status"""
        p, e, n = self.getfullname()
        self.app.setBusy()
        status = self.app.server.updateJob(name=n, prj=p, exp=e)
        self.app.setReady()
        return status

    def getresults(self, cb=None):
        """ download results from the server"""
        self.app.setBusy()
        datadir = self.app.getDockingDir()
        prj, exp, name = self.getfullname()
        destpath = os.path.join(datadir, prj, exp, name)
        # FIXME check if the dir exist?
        # FIXME check if successful before proceding?
        hf.makeDir(fullpath=destpath)
        #self.app.server.downloadResult(self.name, destpath) # XXX why SELF.NAME?
        report = self.app.server.downloadResult(name=name, destpath = destpath, prj=prj, exp=exp)
        if report == False:
            #self.dprint("No files downloaded!")
            # FIXME delete previously created dir?
            pass
        self.app.setReady()
        return report


    def updateDownloadStatus(self):
        """ check the download status with the server download manager """
        return self.app.server.updateDownloadStatus()

    def stopDownload(self):
        """ halt the results download"""
        self.server.stopDownload()

    def deleteresults(self):
        """ the deleteresults method must be implemented by each subclass"""
        #datadir = self.app.getDataDir()
        self.app.setBusy()
        datadir = self.app.getDockingDir()
        destpath = datadir + os.sep + self.name
        shutil.rmtree(destpath)
        self.app.setReady()


    def nuke(self):
        """ remove any information related to the vs """
        self.deleteresults()
        self.deletelocalres()
        self.delete()

    def getMasterLog(self):
        """ retrieve the master log where all jobs are writing"""
        return self.app.server.getMasterLog(self.name)

    def checkServerConnection(self, quiet=False):
        """ check if the current server (if any) hosts
            the job info.
            if not, tries to establish a connection
            with the job's server as from:
                self.properties['hostname']
                bj.properties['servername']
        """
        vshostname = self.properties['hostname']
        vsservername = self.properties['servername']
        #try:
        username = self.properties['username']
        #except:
        #    username = None
        #    print "\n\n\t\tWARNING! OLD HISTORY FILE!\nusername is missing\n\n"
        if not self.app.server == None:
            curr_name = self.app.server.name()
            curr_hostname = self.app.server.hostname()
            curr_username = self.app.server.ssh.username
            if (not curr_hostname == vshostname) or (not curr_username == username):
                newhostname = self.app.findSshServerByHostname(vshostname, username)
                if newhostname == None:
                    t = 'Unknown host'
                    i = 'error'
                    m = ('VS job information cannot be accessed because '
                         'there are no saved connections matching '
                         'the follwing settings:\n\n'
                         '- hostname : %s\n - username : %s\n\n'
                         'Use the Server Manager to create a new server profile '
                         'with required settings and try again.') % (vshostname, username)
                    tmb.showinfo(parent=None, title=t, message=m, icon=i)
                    return False
                if not quiet:
                    t = 'Disconnect from server'
                    i = 'info'
                    m = ('The information to be retrieved is '
                         'not on the current server/account.\n\n'
                         'Disconnect from:\t%s (user: %s)\n\n'
                         'and connect to:\t%s (user : %s)?') % (curr_hostname, curr_username, vshostname, username)
                    if not tmb.askyesno(parent=None, title=t, message=m, icon=i):
                        return False
                self.app.disconnectSshServer()
        if self.app.server == None:
            app_server_name = self.app.findSshServerByHostname(vshostname, username)
            self.app.setupTab.chooseServer(app_server_name)
        if self.app.server == None:
            t = 'Missing server connection'
            i = 'error'
            m = ('VS job information cannot be downloaded because '
                 'it is not possible to connect to server named "%s" (user:%s)'
                 '\n\nCreate a new server profile '
                 'in the Server Manager and try again.') % (vshostname, username)
            tmb.showinfo(parent=None, title=t, message=m, icon=i)
            return False
        if not self.app.server.checkServerStatus():
            return False
        return True


class VirtualScreeningLocal(VirtualScreening):
    """
    """
    pass




# project
#    virtual_screenings 
#       rec_vs ( rec + lig_lib )


class VSresultTree(rb.RaccoonDefaultWidget, DebugTools.DebugObj):

    def __init__(self, parent, app, fname=None, iconpath = None, debug=False):
        DebugTools.DebugObj.__init__(self, debug)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        import Pmw, Tkinter
        import TkTreectrl, ImageTk
        import os
        import tkFont
        #import OpalClient
        #ICONPATH='icons/'
        family = 'Bitstream vera sans'
        #family = 'Arial'
        #self.FONT = tkFont.Font(family=family,size=9) # now Rdb
        self.FONTlargebold = tkFont.Font(family=family,size=11, weight='bold')
        #self.FONTbold = tkFont.Font(family=family,size=9,weight="bold")

        self.app = app

        if iconpath:
            self._iconpath=iconpath
        else:
            from CADD.Raccoon import ICONPATH
            self._iconpath=ICONPATH
        # print "UICONPATH", self._iconpath
        self.initIcons()

        Tkinter.wantobjects=0
        #self.parent = parent

        self._initTree()

        #self.app.eventManager.registerListener(RaccoonEvents.AddJobHistory, self.addTreeItem)  # job history update
        self.app.eventManager.registerListener(RaccoonEvents.UpdateJobHistory, self.updateTreeItem)  # job history update
        self.app.eventManager.registerListener(RaccoonEvents.DeletedJobHystoryItem, self.pruneTree)  # job history update

        #self.app.eventManager.registerListener(RaccoonEvents.SyncJobHistory, self.syncCallback) # update the tree with newly synced items
        # FIXME add registration to updateParent function to be called after these above

        if fname:
            self.setDataFile(fname)

    def initIcons(self):
        """ initialize the icons for the interface"""
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'prj.png'
        self._ICON_prj = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'exp.png'
        self._ICON_exp = ImageTk.PhotoImage(Image.open(f))
        
        f = icon_path + os.sep + 'vs.png'
        self._ICON_vs = ImageTk.PhotoImage(Image.open(f))

###    
###    def syncCallback(self, event=None):
###        """ trigger a refresh of the tree to
###            include newly discovered jobs on 
###            the remote server (syncinc)
###        """
###        print "&&& SYNCCALLBACK CALLED"
###        # FIXME 
###        # self._populateItems(self.app.getHistoryFile() )
###        #def updateTreeItem(self, event=None):
###        #self.expandNode(self.research)
###        print "SELF RESEARCH NOW", self.research.children
###


    def updateTreeItem(self, event=None):
        """ update items in the tree"""
        expand = []
        vsklass = { 'ssh' : VirtualScreeningSsh, 
                    'opal': VirtualScreeningOpal,
                    'local': VirtualScreeningLocal,
                 }
        p, e, j = event.prj, event.exp, event.name
        # project
        prj = self.research.getPrj(event.prj)
        if prj == None:
            prj = Project(event.prj, self.app)
            self.research.addChild(prj)
            expand.append(self.research)

        # experiment
        exp = prj.getExp(event.exp)
        if exp == None:
            exp = Experiment(event.exp, self.app)
            prj.addChild(exp)
            expand.append(prj)

        # vs
        vs = exp.getVs(event.name)
        if vs == None:
            vs = vsklass[event.jtype](event.name, self.app, properties = event.properties)
            exp.addChild(vs)
            expand.append(exp)
        # expanding
        for p in expand:
            self.expandNode(p)
        # FIXME here there shuold be a trigger for updating the status
        # of a project, that recursively will update experiments and jobs
        info = self.app.history[event.prj][event.exp][event.name]
        status = info['status']
        item = self.tree.objToItem.get(vs, None) 
        if item == None:
            return
        txt = self._treeStyles['cell']['txt']
        self.tree.itemelement_config(item, self.tree.columns[1],
            txt, text=status)
        # update parent (exp)
        self.updateExpTree(exp)


        




    def pruneTree(self, event=None):
        """ remove items from tree and trim prj and
            exp branches if empty
        """
        to_test = { 'prj': [], 'exp': [] }
        p = event.prj
        e = event.exp
        j = event.name
        po = self.research.getPrj(p)
        delList = []
        # delete job
        if (not e == None) and (not j == None): # p, e, j
            eo = po.getExp(e)
            jo = eo.getVs(j)
            delList.append(self.tree.objToItem[jo])
            jo.delete()
            if not len(eo.children):
                delList.append(self.tree.objToItem[eo])
                eo.delete()
            if not len(po.children):
                delList.append(self.tree.objToItem[po])
                po.delete()
        # delete experiment
        elif (not e == None) and (j == None): # p, e
            eo = po.getExp(e)
            delList.append(self.tree.objToItem[eo])
            eo.delete()
            if not len(po.children):
                delList.append(self.tree.objToItem[po])
                po.delete()
        # delete project
        elif (e == None) and (j == None): # p
            delList.append(self.tree.objToItem[po])
            po.delete()
        for d in delList:
            self.tree.item_delete(d)
            

    def traverse(self, node):
        if len(node.children)==0: # node is job
            #print 'JOB', node.name
            #query status and update tree for job
            return 'Succeess'
        results = []
        for child in node.children:
            results.append(self.traverse(child))
        return results



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
        """ _populateItems must be overloaded by the 
            inheriting object
        """
        self._populateItems(fname)
        self._activateTree()

    def _activateTree(self):
        self._buildTree()
        self.tree.notify_generate('<Expand-before>', item=TkTreectrl.ROOT)
        self.tree.see(TkTreectrl.ROOT)


    def _populateItems(self, fname):

        projects = hf.readjson(fname)
        if projects  == False:
            print "NO DATA IN THE FILE"
            return

        klass = { 'ssh' : VirtualScreeningSsh,
                  'opal': VirtualScreeningOpal,
                  'local' : VirtualScreeningLocal,
                }

        for k,v in projects.items():
            pro = Project(k, self.app)
            self.research.addChild(pro)
            for ek, ev in v.items():
                exp = Experiment(ek, self.app)
                pro.addChild(exp)
                for name, vsdata in ev.items():
                    _type = vsdata['resource']
                    job = klass[_type](name, self.app, properties=vsdata)
                    exp.addChild(job)


    def _initTree(self):
        #print "INIT TREE"
        self.treeObj = TkTreectrl.ScrolledTreectrl(self.parent)
        border = { 'bd':1,'highlightbackground':'black',
                    'borderwidth':2,'highlightcolor':'black','highlightthickness':1}
        self.treeObj.configure( **border)
        self.treeObj.pack(expand=1,fill='both')
        self.tree = self.treeObj.treectrl

        self.research = Research(self.app)
        self.tree.itemToObj={ TkTreectrl.ROOT : self.research } # gives obj from tree items
        self.tree.objToItem = {self.research : TkTreectrl.ROOT} # give tree items from obj



    def _buildTree(self):

        self.tree.columns = []
        #jobname_col= self.tree.column_create(text="jobname")
        jobname_col= self.tree.column_create(text="",expand=1)
        self.tree.columns.append(jobname_col)
        self.tree.configure(treecolumn=jobname_col, showbuttons=1, font=self.FONT)
        self.tree.columns.append(self.tree.column_create(text='status', expand=0))
        self.tree.columns.append(self.tree.column_create(text='resource', expand=1))
        self.tree.columns.append(self.tree.column_create(text='date', expand=0))
        #self.tree.columns.append(self.tree.column_create(text='resource', expand=0))
        #self.tree.columns.append(self.tree.column_create(text='results URL', expand=1))

        self._prjIcon = prjIcon = self._ICON_prj
                    #ImageTk.PhotoImage(
                    #file=os.path.join(self._iconpath, 'water2.png')) # XXX Keep
                    #file=self._ICON_prj)
        self._expIcon = expIcon = self._ICON_exp
        #self._expIcon = expIcon = ImageTk.PhotoImage(
                    #file=os.path.join(self._iconpath, 'system.png'))
                    #file=self._ICON_exp)
        self._jobIcon = jobIcon =  self._ICON_vs
        #self._jobIcon = jobIcon =  ImageTk.PhotoImage(
        #            file=self._ICON_vs)

        self._treeStyles = {}

        # text style

        # style for project
        styleProject = self.tree.style_create()
        pel_image = self.tree.element_create(type=TkTreectrl.IMAGE,
                                    image=(prjIcon, TkTreectrl.OPEN, prjIcon, ''))

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
        #job_image = self.tree.element_create(type=TkTreectrl.IMAGE,
        #                            image=(jobIcon, TkTreectrl.OPEN, jobIcon, ''))
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
        #                            image=(prjIcon, TkTreectrl.OPEN, prjIcon, ''))
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
        self.tree.bind('<ButtonRelease-3>', self.on_button3)
                

    def expandNode_cb(self, event):
        #print "prj EXAPAND NODECB"
        item = event.item
        obj = self.tree.itemToObj.get(item, None)
        self.expandNode(obj)
            


    def expandNode(self, obj):
        item = self.tree.objToItem.get(obj, None)
        #print "ITEM", item, obj
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
                self.tree.itemstyle_set(new, self.tree.columns[1], c_style)
                self.updateExpTree(child)
###                nbSuccess = nbFail = nbRunning = 0
###                for c in child.children:
###                    #"CSTATUS", c.status
###                    if c.status=='completed': nbSuccess +=1
###                    elif c.status=='killed': nbFail +=1
###                    elif 'running' in c.status: nbRunning +=1
###                if nbSuccess==len(child.children) and nbSuccess > 0:
###                    status = 'successful'
###                    #status = 'SUCCESSFUL'
###                    color = '#33bb33'
###                elif nbFail==len(child.children) and nbFail > 0:
###                    #status = 'FAIL'
###                    status = 'fail'
###                    color = 'red'
###                elif nbRunning == len(child.children) and nbRunning > 0:
###                    status = 'running'
###                    color = 'orange'
###                else:
###                    status = 'PARTIAL'
###                    color = 'orange'
###                #color = 'black'
###                child.status = status
###                self.tree.itemelement_config(new, self.tree.columns[1], c_txt, text=status, fill=(color,),font=self.FONTbold)

            if isinstance(child, VirtualScreening):
                # vs name 
                style = job['style']
                text = job['txt']
                img = job['img']
                #self._treeStyles['job'] = { 'img' : job_image, 'txt' : pel_text, 'style' : styleJob}
                #print child
                self.tree.itemstyle_set(new, self.tree.columns[0], style)
                self.tree.itemelement_config(new, self.tree.columns[0],
                    text, text=child.name, fill=('black',), font=self.FONT)

                # status
                text = cell['txt']
                style = cell['style']
                self.tree.itemstyle_set(new, self.tree.columns[1], style)
                self.tree.itemelement_config(new, self.tree.columns[1],
                    text, text=child.status, fill=('black',), font =self.FONT )

                # resource
                self.tree.itemstyle_set(new, self.tree.columns[2], style)
                resource = "[%s] %s - %s@%s" % (child.resource,
                                                child.properties['servername'], 
                                                child.properties['username'], 
                                                child.properties['hostname'])
                self.tree.itemelement_config(new, self.tree.columns[2], text, text=resource, fill=('black',), font=self.FONT)
                self.tree.itemstyle_set(new, self.tree.columns[3], style)
                date = "%s/%s/%s %s:%s:%s" % tuple(child.date)
                self.tree.itemelement_config(new, self.tree.columns[3], text, text=date, fill=('black',), font=self.FONT)

            ##if isinstance(child, VirtualScreeningSsh):
            ##    self.tree.itemstyle_set(new, self.tree.columns[3], style)
            ##    self.tree.itemelement_config(new, self.tree.columns[3], text, text=child.jobId, fill=('black',), font=self.FONT)
            ##if isinstance(child, VirtualScreeningOpal):
            ##    self.tree.itemstyle_set(new, self.tree.columns[4], style)
            ##    self.tree.itemelement_config(new, self.tree.columns[4], text, text=child.url, fill=('black',), font=self.FONT)
            ##    self.tree.itemstyle_set(new, self.tree.columns[5], style)
            ##    self.tree.itemelement_config(new, self.tree.columns[5], text, text=child.resurl, fill=('black',), font=self.FONT)

    def updateExpTree(self, exp):
        """ update experiment entry in the tree"""
        item = self.tree.objToItem.get(exp, None)
        prj  = self._treeStyles['prj']
        cell = self._treeStyles['cell']
        job  = self._treeStyles['job']

        p_txt = prj['txt']
        p_img = prj['img']
        p_style = prj['style']
        c_txt = cell['txt']
        c_style = cell['style']
        
        run_c = 0
        kill_c = 0
        done_c = 0
        download_c = 0
        tot = len(exp.children)
        runLike = ['submitted', 'collecting', 'running', 'queued', 'held', 'held/queued']
        killLike = ['killed', 'deleted', 'unknown job']
        status = "mixed"
        color = 'black'
        report = []
        for child in exp.children:
            s = self.getJobInfo(child)['status']
            report.append(s)
            if 'running' in s or s in runLike:
                run_c += 1
            elif s in killLike:
                kill_c += 1
            elif s =='completed' or s =='downloaded':
                done_c += 1
            #elif s == 'downloaded': 
            #    download_c += 1
        if run_c > 0: # something still running
            status = 'running'
            color = '#ff9900'
        else:
            if kill_c == tot: # all killed
                status = 'killed/deleted'
                color = '#bb3333'
            elif done_c > 0: # nothing running, something completed
                status = 'completed'
                color = '#33bb33'
        #print "SATATYS", status, done_c, kill_c, run_c
        #print "REPORTING STATUS", report
        self.tree.itemelement_config(item, self.tree.columns[1], c_txt, text=status, fill=(color,),font=self.FONTbold)


    def on_button3(self,event):
        """ manage the rmb calls, identify the item (if any) under the cursor
            and and dispatch the menu call.
        """
        t = event.widget
        #position = (event.widget.winfo_parentx()+event.x, event.widget.winfo_rooty()+event.y)
        position = (event.x_root, event.y_root)
        identify = t.identify(event.x, event.y)
        # identify might be None or look like:
        # ('item', '2', 'column', '0') or ('item', '3', 'column', '0', 'elem', 'pyelement3')
        if identify:
            try:
                item, column, element = identify[1], identify[3], identify[5]
                if item == 0: # it's root
                    #print "ROOT FOUND"
                    return
                #if True:
                try:
                    obj = self.tree.itemToObj[item]
                    self._postMenu(position, obj)
                except: 
                #else:
                    print "missing item, probably parent", item
                    print sys.exc_info()[1]
                    return
            except IndexError:
                pass


    def _postMenu(self, position, obj):
        """ post the different menus depending on the obj instance"""
        if isinstance(obj, Project):
            self._prjMenu(position, obj)
        elif isinstance(obj, Experiment):
            self._expMenu(position, obj)
        elif isinstance(obj, VirtualScreeningLocal):
            self._vsLocalMenu(position, obj)
        elif isinstance(obj, VirtualScreeningOpal):
            self._vsOpalMenu(position, obj)
        elif isinstance(obj, VirtualScreeningSsh):
            self._vsSshMenu(position, obj)


    # project commands
    def _prjMenu(self, position, obj):
        """ post the option menu for a project"""
        cb_update = CallbackFunction(self._prj_update, (obj))
        cb_download = CallbackFunction(self._prj_download, (obj))
        cb_del = CallbackFunction(self._prj_delete, (obj))
        cb_kill = CallbackFunction(self._prj_kill, (obj))
        #cb_p = CallbackFunction(self._prj_properties, (obj))

        content = [ ['Project'],
                    ['Update status', 'normal', cb_update],
                    ['Download results', 'normal', cb_download],
                    [  ],
                    ['Kill all jobs', 'normal', cb_kill],
                    ['Delete project', 'normal', cb_del],
#                    [  ],
#                    ['Properties', 'normal', cb_p],
                  ]
        m = rb.RacMenu(self.tree, content, placement=position, floating=True)
        m()


    def _prj_update(self, obj, event=None):
        """ "update project status by updating all 
            experiments and jobs contained within it
        """
        skip_list = ['downloaded', 'completed', 'killed']
        for c in obj.children:
            s = self._exp_update(c)
            if not s:
                #print "UPDATE EXP CHILDREN returned error"
                return
        
    def _prj_download(self, obj, event=None):
        """ download all jobs that are completed"""
        for c in obj.children:
            self._exp_download(c)

    def _prj_kill(self, obj, event=None):
        """ kill all jobs that are still running"""
        t = 'Kill jobs'
        i = 'warning'
        m = ('All running jobs in the project '
             'are going to be killed.\n\nContinue?')
        if not tmb.askyesno(parent=self.treeObj, title=t, message=m, icon=i):
            return
        for c in obj.children:
            self._exp_kill(c, silent=True)

    def _prj_delete(self, obj, event=None):
        """ delete all jobs contained in the project"""
        t = 'Delete project'
        i = 'warning'
        m = ('All data of jobs in the project '
             'is going to be deleted.\n\nContinue?')
        if not tmb.askyesno(parent=self.treeObj, title=t, message=m, icon=i):
            return
        to_delete = obj.children[:]
        for c in to_delete:
            self._exp_delete(c, silent=True)

#    def _prj_properties(self, obj, event=None):
#        """ show project properties"""
#        pass


    # /project commands

    # experiment commands
    def _expMenu(self, position, obj):
        """ post the option menu for a project"""
        cb_update = CallbackFunction(self._exp_update, (obj))
        cb_download = CallbackFunction(self._exp_download, (obj))
        cb_del = CallbackFunction(self._exp_delete, (obj))
        cb_kill = CallbackFunction(self._exp_kill, (obj))
        #cb_p = CallbackFunction(self._exp_properties, (obj))
        content = [ ['Experiment'],
                    ['Update status', 'normal', cb_update],
                    ['Download results', 'normal', cb_download],
                    [  ],
                    ['Kill all jobs', 'normal', cb_kill],
                    ['Delete experiment', 'normal', cb_del],
                    #[  ],
                    #['Properties', 'normal', cb_p],
                  ]
        m = rb.RacMenu(self.tree, content, placement=position, floating=True)
        m()

    def _exp_update(self, obj, event=None):
        """ update all jobs contained in the experiment"""
        self.app.setBusy()
        for c in obj.children:
            s = self._vs_update(c)
            if not s:
                self.dprint("children %s said no updates..." % obj.name)
        self.app.setReady()

    def _exp_download(self, obj, event=None, silent=False):
        """ download all completed jobs within"""
        process = []
        jobs = []
        for c in obj.children:
            info = self._is_downloadable(c)
            if info:
                process.append(c)
                jobs.append(info)
        if not len(process) and not silent:
            t = 'Download experiment'
            i = 'info'
            m = 'The experiment does not contain jobs that can be downloaded'
            tmb.showinfo(parent=self.treeObj, title=t, icon=i, message=m)
            return False
        self.app.setBusy()
        ResultsDownloadGUI(parent = self.treeObj, app=self.app, objlist = process, auto=True)
        toprocess = []
        for o in process:
            report = self._is_downloaded(o)
            if report:
                toprocess.append(report)
        self.autoProcessResults(jobs = toprocess)
        # unregister job from the server
        leftovers = []
        for p,e,j in jobs:
            if self.app.history[p][e][j]['status'] == 'downloaded':
                self.app.server.unregisterJob(name=j, prj=p, exp=e, removefiles=True)
            else:
                leftovers.append((p,e.j))
        if len(leftovers):
            t = 'Data not removed'
            i = 'warning'
            m = ('The data of %s jobs in experiment [%s] '
                 'have not been removed from the server '
                 'due to possible issues in the download.\n'
                 'Inspect the remote files, then download '
                 'and process them manually')
            tmb.showinfo(parent=self.treeObj, title=t, icon=i, message=m)
        self.updateExpTree(obj)
        self.app.setReady()
        return True

    def _is_downloadable(self, obj):
        """ obj is a vs job, return true if results are downloadable"""
        self.dprint("called with [%s]" % obj)
        p,e,n = self.vsObjToTuple(obj)
        if self.app.history[p][e][n]['status'] == 'completed':
            return p,e,n
        return False

    def _is_downloaded(self,obj):
        """ obj is a vs job, return true if results are downloadable"""
        p,e,n = self.vsObjToTuple(obj)
        self.dprint("Checking [%s][%s][%s]" % (p,e,n))
        if self.app.history[p][e][n]['status'] == 'downloaded':
            return p,e,n
        return False


    def _exp_kill(self, obj, event=None, silent=False):
        """ kill children jobs"""
        if not silent:
            t = 'Kill jobs'
            i = 'warning'
            m = ('All running jobs in the experiment '
                 'are going to be killed.\n\nContinue?')
            if not tmb.askyesno(parent=self.treeObj, title=t, message=m, icon=i):
                return
        for c in obj.children:
            self._vs_kill(c, silent=True)

    def _exp_delete(self, obj, event=None, silent=False):
        """ delete children jobs"""
        if not silent:
            t = 'Delete experiment'
            i = 'warning'
            m = ('All data of jobs in the experiment '
                 'is going to be deleted.\n\nContinue?')
            if not tmb.askyesno(parent=self.treeObj, title=t, message=m, icon=i):
                return
        to_delete = obj.children[:]
        #print "DELETING THIS GUYS", to_delete
        for c in to_delete:
            #print "\n\n==================CCC", c
            self._vs_delete(c, silent=True)
    # /experiment commands

    def vsObjToTuple(self, obj, string = True):
        """ return the tuple of (prj,exp,vsname) as string 
            for a vs object; if string == true, return the
            objects
        """
        self.dprint("called with [%s]" % (obj))
        name = obj.name
        e_obj = obj.parent()
        p_obj = e_obj.parent()
        self.dprint("processing p[%s] e[%s] j[%s]" % (p_obj.name, e_obj.name, obj.name))
        if string:
            return tuple([ x.name for x in (p_obj, e_obj, obj) ])
        return (p_obj, e_obj, obj)

    def getJobInfo(self, obj):
        """ retrieve job info from a vs object"""
        p, e, n = self.vsObjToTuple(obj)
        return self.app.history[p][e][n]

    def _vsSshMenu(self, position, obj):
        """ post the option menu for the vs ssh"""
        # TODO scan the obj first then add only useful options

        jobInfo = self.getJobInfo(obj)
        status = jobInfo['status']
        up_status = dw_status = rs_status = k_status= d_status = 'normal'
        if ('running' in status) or (status == 'submitted'):
            dw_status = rs_status = 'disabled'
        elif status == 'killed':
            up_status = dw_status = k_status = 'disabled'
        elif status == 'completed':
            up_status = k_status = rs_status = 'disabled'
        elif status == 'downloaded':
            up_status = dw_status = k_status = 'disabled'
        elif status == 'deleted': # the job files can't be found on the server
                                  # i.e. deleted outside raccoon
            up_status = dw_status = k_status = 'disabled'
        cb_update = CallbackFunction(self._vs_update, (obj))
        cb_download = CallbackFunction(self._vs_download, (obj))
        cb_restart = CallbackFunction(self._vs_restart, (obj))
        cb_kill = CallbackFunction(self._vs_kill, (obj))
        cb_delete = CallbackFunction(self._vs_delete, (obj)) # only remote files
        cb_properties = CallbackFunction(self._vs_properties, (obj))

        content = [ ['Virtual Screening (SSH)'],
                    ['Update status', up_status, cb_update],
                    ['Download results', dw_status, cb_download],
                    ['Restart job', rs_status, cb_restart],
                    [  ],
                    ['Kill', k_status, cb_kill],
                    ['Delete job', d_status, cb_delete],
                    [  ],
                    ['Properties', 'normal', cb_properties],
                  ]
        m = rb.RacMenu(self.tree, content, placement=position, floating=True)
        m()

    def _vs_restart(self, obj, event=None, quiet=False):
        """ remove .killed file (if exists)
            find submission job
            repeat submission
        """
        # FIXME: set engine, set resource...
        acceptable = ['downloaded', 'killed', 'unknown job']
        p, e, n = self.vsObjToTuple(obj)
        info = self.app.history[p][e][n]
        status = info['status']
        if not status in acceptable:
            print "UNACCEPTABLE STATUS!", status
            reason = ('The current job status [%s] does not allow restarting.\n\n'
                      'Acceptable states are: %s' )
            reason = reason % (status, " and ".join(acceptable))
            self._restartAbortMsg(reason=reason)
            return False
        ## connect to server
        if not obj.checkServerConnection():
            self._restartAbortMsg(reason='Error in the server connection.')
            return False
        # unregister the job from the server (to clean up files)
        if status == 'killed':
            self.app.server.unregisterJob(n, p, e, removefiles=True)
        ## select docking service
        if not self._restart_setService(jobinfo=info):
            return False
        ## select library
        if not self._restart_setLibrary(jobinfo=info):
            return False
        ## select receptors
        if not self._restart_setReceptor(jobinfo=info):
            return False
        # set config settings
        if not self._restart_setConfig(jobinfo=info):
            return False
        suggest = {'prj' : p, 'exp': e}
        #EE_jobmanager.JobSubmissionInterface(self.treeObj, jmanager=self, app = self.app, suggest=suggest)
        self.app.jobmanTab.submit(suggest = suggest)
        # FIXME check if Triggere event to delete results from the analysis?
        return True

    def _restart_setConfig(self, jobinfo):
        """ restore config settings"""
        # write a config file
        configfile = os.path.join(self.app.getTempDir(), 'config.conf')
        fp = open(configfile, 'w')
        for k,v in jobinfo['config'].items():
            fp.write("%s = %s\n" % (k,v))
        fp.close()
        # load config file (cumbersome but works)
        if self.app.configTab._loadvinaconf(configfile, quiet=True) == False:
            self._restartAbortMsg(reason='Error in the docking config step.')
            return False
        return True

    def _restart_setService(self, jobinfo):
        """ contact the setup tab to ask if 
            servicename is available on the server
            and set it as in use
        """
        service = jobinfo['service']
        self.dprint("Service requested [%s]" % service)
        if not self.app.server.services(name=service):
            m = ('The docking service "%s" '
                'is not available on the server.')
            m = m % service
            self._restartAbortMsg(reason=m)
            return False
        self.app.setupTab._service_choice.set(service)
        self.app.setupTab.setService() # trigger event and callbacks
        return True

    def _restart_setLibrary(self, jobinfo): 
        """ set the library from the server"""
        # FIXME for now only single (first) lib loaded
        # FIXME for now only ssh libraries are selected 
        #       (we need a more generalized lib call)
        lib = jobinfo['ligsource'][0]
        selected = {'libname' : lib['name'], 'filters' : lib['filters']}
        #libname = lib['name'], filters=lib['filters']):
        if not self.app.ligandTab.libselect_cb_ssh(**selected):
            m = ('Error in the library selection.\n\n'
                 'The library "%s" is not available '
                'on the server') % lib['name']
            self._restartAbortMsg(reason=m)
            return False
        return True

    def _restart_setReceptor(self, jobinfo):
        """ take care of setting the receptor(s)"""
        # remove previous receptors
        self.app.receptorTab.deletefiles(nuke=True)
        fingerp = jobinfo['recfingerp']
        alias = jobinfo['receptor']
        success, recfile = self.app.getTargetCacheFile(fingerp, alias)
        if not success:
            self._restartAbortMsg(reason='Error in copying the receptor.')
            return False
        # FIXME check returned value?
        self.app.receptorTab.openfiles(files=[recfile], quiet=True)
        return True

    def _restartAbortMsg(self, event=None, reason=None):
        """ return the standard answer for failed restarted job"""
        t = 'Job restart failure'
        i = 'info'
        #m = ('The job re-submission interrupted.')
        m = ''
        if not reason == None:
            m += "\n\n" + reason
        tmb.showinfo(parent=self.treeObj, title=t, message=m, icon=i)


    def _vs_properties(self, obj, event=None):
        """ show all properties of a job"""
        # select which keywords exclude
        exclude = ['masterlog', 'type' , 'statusfile', 'summary']
        compResource = { 'ssh' : 'Linux cluster', 
                        'local' : 'local machine', 
                        'opal' : 'Opal server'}
        p, e, n = self.vsObjToTuple(obj)
        info = self.app.history[p][e][n]
        data = [] # [ ['Project', p], ['Experiment', e], ['Name', n] ]
                
        for k,v in info.items():
            if not k in exclude:
                if k == 'date':
                    v = "%s/%s/%s %s:%s:%s" % tuple(v)
                    k = 'submission date'
                elif k == 'total':
                    k = 'total ligands'
                elif k == 'jobid':
                    k = 'job Id(s)'
                    #v = "\n ".join(v)
                    v = hf.listToString(v, sep=', ', wide=10)
                elif k == 'config':
                    txt = ""
                    for a in sorted(v.keys()):
                        if not a == 'receptor':
                            txt += " %s : %s\n" % (a,v[a])
                    v = txt[:-1]
                elif k == 'vsdir':
                    k = 'remote directory'
                elif k == 'recfingerp':
                    k = 'receptor fingerprint'
                elif k == 'resource':
                    k = 'computational resource'
                    v = compResource.get(v, 'unknown')
                elif k == 'ligsource':
                    k = 'Ligand sources'
                    txt = []
                    line = "library: %s\tfilters: %s"
                    for i in v:
                        txt.append(line % (i['name'], i['filters']))
                    v = "\n".join(txt)
                        
                k = str(k) + " "
                v = " " + str(v)
                data.append([k.title(), v])
        data.sort(key=itemgetter(0))
        win = Pmw.Dialog(parent=self.parent, title="Job information", buttons=('Close',))
        bbox = win.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)
        w = win.interior()
        cont = tk.Frame(w, relief='sunken', **self.BORDER)
        f = tk.Frame(cont)
        s = tk.Frame(cont, relief='flat', **self.BORDER)
        x = tk.Frame(cont) #, **self.BORDER)
        # project
        tk.Label(f, text='Project ', font=self.FONTbold, anchor='e', 
            justify='right').pack(side='top', anchor='e')
        tk.Label(x, text=" " + p, font=self.FONT, anchor='w', justify='left',
            bg='white').pack(side='top', anchor='w', expand=1, fill='x')
        # experiment
        tk.Label(f, text='Experiment ', font=self.FONTbold, anchor='e', 
            justify='right').pack(side='top', anchor='e')
        tk.Label(x, text=" " + e, font=self.FONT, anchor='w', justify='left',
            bg='white').pack(side='top', anchor='w', expand=1, fill='x')

        # experiment
        tk.Label(f, text='Job ', font=self.FONTbold, anchor='e',
            justify='right').pack(side='top', anchor='e')
        tk.Label(x, text=" " + n, font=self.FONT, anchor='w', justify='left',
            bg='white').pack(side='top', anchor='w', expand=1, fill='x')
        f.pack(expand=0,fill='none',anchor='w', side='left')
        s.pack(expand=0,fill='y',anchor='n', side='left')
        x.pack(expand=1,fill='x',anchor='w', side='left')
        cont.pack(expand=0,fill='x',anchor='w', side='top', padx=8,pady=4)

        #text = "Project:\t%s\nExperiment:\t%s\nJob:\t%s" % (p,e,n)
        #tk.Label(w, text=text, font=self.FONTbold, anchor='w', justify='right').pack(anchor='n', side='top')
        f = tk.Frame(w)
        tab = hf.SimpleTable(f, title_item='column', cell_justify='w', title_justify='e',
                title_color ='#d8daf8', cell_color='white',  title_width=30,
                title_font = self.FONTbold, cell_font=self.FONT,
                autowidth=True)
        tab.setData(data)
        f.pack(expand=0,fill='none',anchor='n', side='top', padx=8,pady=8)
        #print win.component('buttonbox')
        win.activate()



    def _vs_update(self, obj, event=None):
        """ manage the operations related to updating job status"""
        skip_list = ['downloaded', 'completed', 'killed']
        p, e, n = self.vsObjToTuple(obj)
        status = self.app.history[p][e][n]['status']
        if status in skip_list:
            return False
        if not obj.checkServerConnection():
            return False
        status = obj.getstatus() # XXX do update
        name = obj.name
        if isinstance(status, float):
            if status == 100:
                status = 'completed'
            else:
                status = 'running (%2.1f%%)' % status
        prop = { 'status': status }
        self.app.updateJobHistory(n, p, e, properties=prop)
        # XXX propagate event
        #e = RaccoonEvents.UpdateJobHistory()
        #self.app.eventManager.dispatchEvent(e)
        # XXX FIXME 
        # here there should be a call to self.updateParent()
        self.updateExpTree(obj.parent())
        return True

    def checkJobHealth(self, status):
        """ return if a job is in good shape or not
            if not, it's not worth to proceed with
            expensive functions (update status, download,
            etc...)
        """
        bad_shape = ['dead', 'killed','unknown job']
        return not (status in bad_shape)


    def _vs_download(self, obj, event=None, autoprocess=True, silent=False):
        """ manage results download
            
            autoprocess : process results automatically to generate summary
            silent      : do not issue messages (i.e. when invoked by parents)
        """
        messages = { 'already' : ('Results have been already downloaded.\n'
                                  'Do you want to download them again?'),
                     'still'   : ('The job is still running, try again later.'),
                     'other'   : ('There are no results for this job\n[status:"%s"]'),
                    }
        t = 'Results download'
        prj, exp, name = self.vsObjToTuple(obj)
        # retrieve info to check if it is in an useful status
        info = self.app.history[prj][exp][name]
        status = info['status']
        if status == 'downloaded':
            if not silent:
                i = 'warning'
                m = messages['already']
                if not tmb.askyesno(parent = self.parent, title=t, icon=i, message=m):
                    return False
            else:
                return True
            status = 'completed'
        if not status == 'completed':
            if not self.checkJobHealth(status):
                if not silent:
                    i = 'info'
                    m = messages['other'] % status
                    tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
                return False
            # update status
            if not self._vs_update(obj):
                return False
            status = self.app.history[prj][exp][name]['status']
            if not status == 'completed':
                if not silent:
                    i = 'info'
                    m = messages['other'] % status
                    tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
                return False
        self.app.setBusy()
        # download the files from the server
        ResultsDownloadGUI(parent = self.treeObj, app=self.app, objlist = [obj], auto=True)
        # check that job status has been updated (=success)
        if not self.app.history[prj][exp][name]['status'] == 'downloaded':
            t = 'Download issues'
            i = 'error'
            m = ('It was not possible to download the results.\n\n'
                 'Inspect the job remote directory for issues.'
            )
            tmb.showinfo(parent=self.treeObj, title=t, message=m, icon=i)
            self.app.setReady()
            return False
        # process data locally # TODO this should be a dedicated function
        if autoprocess:
            job = [ prj, exp, name ]
            self.app.setBusy()
            success = self.autoProcessResults(jobs = [ job ] )
            if success == [ True ] : 
                # unregister job from the server
                self.app.server.unregisterJob(name, prj, exp, removefiles=True)
                self.app.setReady()
                return True
            else:
                self.dprint("Problematic result, data not deleted from server")
            self.app.setReady()
            return False
        else:
            # unregister job from the server
            self.app.server.unregisterJob(name, prj, exp, removefiles=True)
            self.app.setReady()
            return True
        return True

    def _vs_kill(self, obj, event=None, silent=False):
        """ kill runing job
            return True for success or not problematic results
                   False for any problems
        """
        prj, exp, name = self.vsObjToTuple(obj)
        if not silent:
            t = 'Killing job' 
            i = 'warning'
            m = ('The following job is going to be killed:\n\n'
                 '%s\n\n'
                 'Proceed?') % name
            if not tmb.askyesno(parent = self.parent, title=t, icon=i, message=m):
                return


        # update to be sure it didn't finished in the meantime
        if not self._vs_update(obj):
            return False
        skip_list = ['downloaded', 'completed', 'killed']
        t = 'Job killing'
        # check that the status is not bad
        # retrieve info to check if it is in an useful status
        status = self.app.history[prj][exp][name]['status']
        if status in skip_list:
            self.dprint("job not killable: status[%s]" % status)
            if not silent:
                i = 'info'
                m = ('The selected job cannot be killed '
                     'because its current status is "%s".') % status
                tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
            return True
        if not obj.checkServerConnection():
            return


        report = self.app.server.killJob(name, prj, exp)
        if not report:
            if not silent:
                i = 'error'
                m = 'There was an unknown error trying to kill the job.'
                tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
            return False
        out, err = report
        if len(err):
            if not silent:
                i = 'error'
                m = ('There was an error trying '
                    'to kill the job:\n\n%s') % ("\n".join(err) )
                tmb.showinfo(parent=self.parent, title=t, message=m, icon=i)
            return False
        self.app.server.unregisterJob(name, prj, exp, removefiles=True)
        self.app.updateJobHistory(name, prj, exp, {'status': 'killed'})
        return True

    def _vs_delete(self, obj, event=None, force=False, silent=False):
        """ delete local and remote files of a job
            
            NOTE: security check is performed here, then  _vs_delete() 
            is called with 'silent' and 'force' as True
        """
        # check that status is useful
        safe_list = ['downloaded', 'killed' ]
        prj, exp, name = self.vsObjToTuple(obj)
        status = self.app.history[prj][exp][name]['status']
        if not force and not silent:
            t = 'Deleting job' 
            i = 'warning'
            m = ('All job files are going to be deleted including files '
                 'on the remote server, and calculations still running will be '
                 'killed.\n\n*All data will be lost*\nProceed?')
            if not tmb.askyesno(parent = self.parent, title=t, icon=i, message=m):
                return
        self.dprint("checking connection")
        if not obj.checkServerConnection():
            return

        self.dprint("unregistering from server")
        # delete files on the remote server
        self.app.setBusy()
        self.app.server.unregisterJob(name, prj, exp, removefiles=True, kill=True)
        self.dprint("unregistering from client")
        # delete local files
        self.app.unregisterJob(name, prj, exp, removefiles=True)
        self.app.setReady()

        # trigger update of the tree
        self.app.setBusy()
        e = RaccoonEvents.DeletedJobHystoryItem(name=name, prj=prj, exp=exp)
        self.app.eventManager.dispatchEvent(e)
        self.app.setReady()
        # FIXME update of the tree item status? (PARTIAL, etc)


    def autoProcessResults(self, jobs):
        """ automate processing of 
            downloaded/completed jobs
        """
        report = []
        for j in jobs:
            processed = EF_resultprocessor.ProcessResultsGui(parent=self.parent, app=self.app, job=j, auto=True)
            report.append(processed.status)
            logfile = processed.logfile
        return report



class ResultsDownloadGUI(rb.RaccoonDefaultWidget, DebugTools.DebugObj):
    # FIXME rewrite to use the new ProgressDialogWindowTk
    def __init__(self, parent, app, objlist, auto=True, debug=False):
        """ """
        rb.RaccoonDefaultWidget.__init__(self, parent)
        DebugTools.DebugObj.__init__(self, debug)

        self.app = app
        self.objlist = objlist
        self.auto = auto

        self._sleep = .5 # sleep time when updating downloads
        self.dialog = Pmw.Dialog(self.parent,
            buttons = ('Stop',), defaultbutton='Stop',
            title = 'Downaloding results',
            command = self.stop)
        d = self.dialog.interior()
        f = tk.Frame(d)
        #tk.Label(d, text='VS result:', font=self.FONTbold,
        #    ).pack(expand=0,fill='none', anchor='w', side='top')
        # name
        tk.Label(f, text='Name ', anchor='e', font=self.FONTbold).grid(row=1,
            column=1,sticky='e')
        self.name = tk.Label(f, text='', font=self.FONT, anchor='w', 
            justify='left',bg='white', width=30, **self.BORDER)
        self.name.grid(row=1,column=2, sticky='w')
        # status
        tk.Label(f, text='Status ', anchor='e', font=self.FONTbold).grid(row=2,
            column=1,sticky='e')
        self.status = tk.Label(f, text='connecting...', font=self.FONT, anchor='w', 
            justify='left',bg='white', width=30, **self.BORDER)
        self.status.grid(row=2,column=2, sticky='w')
        # progress
        tk.Label(f, text='Progress ', anchor='e', font=self.FONTbold).grid(row=3,
            column=1,sticky='e')
        self.counter = tk.Label(f, text='', font=self.FONT, anchor='w', 
            width=30, justify='left',bg='white', **self.BORDER)
        self.counter.grid(row=3,column=2, sticky='w')
        f.pack(expand=0,fill='y',anchor='w', side='top')
        # progress bar
        self.pc_var = tk.DoubleVar(value=0.)
        f = tk.Frame(d)
        self.bar = hf.ProgressBar(f, self.pc_var, w=300)
        self.bar.pack(expand=1, fill='x',anchor='n', side='top',padx=9,pady=3)
        f.pack(expand=1,fill='x', anchor='n', side='top')
        # starting...
        self.STOP = False
        self.dialog.interior().after(100, self.start)
        self.dialog.activate() #geometry= 'centerscreenalways')

    def updateButton(self, event=None):
        """ change the button Stop-> Close"""
        if self.auto:
            self.close()
        bbox = self.dialog.component('buttonbox') 
        i = bbox.index(Pmw.DEFAULT)
        b = bbox.button(i)
        b.configure(text='Close', command=self.close)

    def stop(self, event=None):
        """ """
        p = self.dialog.interior()
        t = 'Confirmation'
        i = 'warning'
        m = 'Stop the current download?'
        if not tmb.askyesno(parent=p,title=t, message=m, icon=i):
            return
        self.STOP = True
        self.updateButton()

    def updateLabel(self, text):
        """ update the label with the name"""
        self.status.configure(text=text)

    def close(self, event=None):
        """ destroy the widget"""
        self.dialog.deactivate()

    def start(self, event=None):
        """ """
        self.dprint("Starting download processes...")
        c = 1
        tot = len(self.objlist)
        for obj in self.objlist:
            # update name
            name = obj.name
            self.name.configure(text='%s' % (name) )
            # update operation
            self.status.configure(text='connecting...')
            if not obj.checkServerConnection():
                continue
            # update counter
            self.status.configure(text='connected')
            self.counter.configure(text='[%d/%d]' % (c, tot ) )
            self.status.configure(text='downloading...')
            report = obj.getresults(cb=self.updateLabel)
            print "REPORT IS THIS!~", report
            if not report == False:
                status = 0
                while status < 100.:
                    if self.STOP:
                        obj.stopDownload() 
                        self.dprint("Removing local files")
                        self.status.configure(text='stopped (deleting temp files)')
                        obj.deletelocalres()
                        return
                    status = obj.updateDownloadStatus()
                    self.pc_var.set(status)
                    time.sleep(self._sleep)
                c += 1
                self.status.configure(text='done.')
                properties = {'status': 'downloaded'}
                p,e,n = obj.getfullname()
                self.app.updateJobHistory(name=n, prj=p, exp=e, properties=properties)
                self.dprint("download completed, status updated")
            else:
                self.dprint("problems in dowload, no status update")
        self.updateButton()

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
