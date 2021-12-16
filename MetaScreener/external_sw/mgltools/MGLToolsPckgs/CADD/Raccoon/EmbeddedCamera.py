


   
from Pmv.moleculeViewer import MoleculeViewer
from DejaVu import Viewer
from ViewerFramework import VFGUI
#from DejaVu.Box import Box # THIS GOES INTO THE CODE THAT CREATES THE BOX
from MolKit import Read
from Tkinter import Toplevel

class EmbeddedMolViewer:

    def __init__(self, target=None,        # Tk container
                       name = '',
                       debug = 0,
                       customrc = None,
                ):
        self.debug = debug
        if self.debug:
            print "EmbeddedMolViewer __init__> ", target
        self.target = target
        self.PMV_win = Toplevel()
        self.PMV_win.withdraw()
        VFGUI.hasDnD2 = False
        print "\n\n--------[ Initializing PMV ]-----------"
        if customrc == None:
            customrc = '_rac_pmvrc'
            
        self.mv = MoleculeViewer(logMode = 'overwrite',  master=self.PMV_win, customizer=customrc,
                title='[embedded viewer]',
                withShell=False,
                verbose=False, gui = True, guiVisible=1)
        print "--------------[ done ]---------------"
        self.VIEWER = self.mv.GUI.VIEWER
        self.GUI = self.mv.GUI
        self.VIEWER.cameras[0].suspendRedraw = 1 # stop updating the main Pmv camera
        self._cam_counter = 0
        self.cameras = {} # 0 : { 'name' : 'grid box viewer' ,
                             #       'obj'  :  'pmv._xx_',
                             #       ''     :

        self.cameraslist = []    # 0, 1, 2 
                                 # keep the order in which cameras are added

        self._pmv_suspended_cams = []
        self.target = target

        if self.target:
            self.addCamera(target = self.targer, name=name)

    def _showPmv(self, event=None):
        if self.debug:
            print "_showPmv> called"
            print "ACTIVE CAMS", self.activeCams()
        self.VIEWER.cameras[0].suspendRedraw = 0 # enable updating the main Pmv camera
        self._pmv_suspended_cams = self.activeCams()

        self.deactivateCam()
        self.mv.GUI.ROOT.deiconify()
        self.VIEWER.cameras[0].Redraw()

    
    def _hidePmv(self, event=None):
        self.VIEWER.cameras[0].suspendRedraw = 1 # stop updating the main Pmv camera
        self.mv.GUI.ROOT.withdraw()
        self.activateCam(self._pmv_suspended_cams) # = self.activeCams()

    def addCamera(self,target,name = ''):
        if self.debug: print "adding another camera"

        c = self.VIEWER.AddCamera(master=target)       # the next ones will be added)
        cam = self.VIEWER.cameras[-1]
        self.cameraslist.append( cam )
        self.cameras[self._cam_counter] = { 'name':name, 'obj':c }
        self._cam_counter += 1
        return cam


    def delCamera(self, idx=None, name=None):
        if self.debug: print "delcamera", idx, name
        if idx == None and name == None:
            print "delete camera by name or by idx!"
            return
        if idx == 0 or len(self.VIEWER.cameras) == 0:
            print "cowardly refusing to delete the main Pmv camera...(returning)"
            return

        #print "CAMERAS _PRE"
        #print self.cameraslist
        #print self.cameras
        #print "============\n\n"
        self.VIEWER.DeleteCamera(idx)
        self.cameraslist.pop( self.cameraslist.index(idx) )
        del self.cameras[idx]
        #print "CAMERAS _PRE"
        #print self.cameraslist
        #print self.cameras
        #print "============\n\n"

 
    def activeCams(self):
        active = []
        for c in self.cameras.keys():
            if not self.cameras[c]['obj'].suspendRedraw:
                active.append(  self.cameras[c]['name'] )
        return active

    def cams(self):
        return [ self.cameras[i]['name'] for i in self.cameras.keys()] 
        
    def camByName(self,name):
        for c in self.cameras.keys():
            if self.cameras[c]['name'] == name:
                return self.cameras[c]['obj']


    def activateCam(self, namelist=[], only=1):
        # - hide/delete all res molecules
        # - reactivate this camera
        if self.debug: print "activatecam> namelist", namelist
        for c in self.cameras:
            if self.cameras[c]['name'] in namelist:
                self.cameras[c]['obj'].suspendRedraw = 0
                self.cameras[c]['obj'].Redraw()
            elif only:
                self.cameras[c]['obj'].suspendRedraw = 1

    def deactivateCam(self, namelist=[]):
        if len(namelist) == 0:
            namelist = self.cameras.keys()
        for c in namelist:
            self.cameras[c]['obj'].suspendRedraw = 1



if __name__ == '__main__':
    
    import Tkinter
    import Pmw
    root = Tkinter.Tk()
    print "\nINITIALIZING VIEWER...\n\n"
    print "PRINT ELLIPSIS", unicode(u"\u2026")
    vi = EmbeddedMolViewer(debug=1)
    print "[ done ]"
    root.bind('Escape', vi._showPmv)
    root.bind('Backspace', vi._hidePmv)
    group  = Pmw.Group(root, tag_text = 'Cameras')
    group.pack(expand=1,fill='both',side='bottom')
    Tkinter.Button(root, text='Add camera...', command = lambda : vi.addCamera(target=group.interior()) ).pack(anchor='w',side='left')
    Tkinter.Button(root, text='Del camera...', command = lambda : vi.delCamera(idx = vi.cameraslist[-1]) ).pack(anchor='w',side='left')
    root.mainloop()

