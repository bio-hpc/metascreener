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
from Pmv.moleculeViewer import MoleculeViewer
from DejaVu import Viewer
from ViewerFramework import VFGUI
from MolKit import Read
from Tkinter import Toplevel
from mglutil.util.callback import CallbackFunction 
from DejaVu.Geom import Geom
from MolKit.molecule import Molecule 
import sys

# XXX XXX
# bind_all to show/hide PMV?

class EmbeddedMolViewer:

    def __init__(self, target=None,        # Tk container
                       name = 'Embedded camera',
                       debug = 0,
                ):
        self.debug = debug
        if self.debug:
            print "EmbeddedMolViewer __init__> ", target
        self.target = target
        self.PMV_win = Toplevel()
        self.PMV_win.withdraw()
        VFGUI.hasDnD2 = False
        print "\n=========================================="
        print "      Initializing PMV..."
        self.mv = MoleculeViewer(logMode = 'overwrite',  master=self.PMV_win, # customizer='custom_pmvrc', 
                title='[embedded viewer]',
                withShell=False,
                verbose=False, gui = True, guiVisible=1)
        self.VIEWER = self.mv.GUI.VIEWER
        self.GUI = self.mv.GUI
        self.VIEWER.cameras[0].suspendRedraw = 1 # stop updating the main Pmv camera
        self._pmv_visible = False
        self.cameras = {}   # 'name' {'obj' : pmv_obj, 'structures': [mol1_obj, mol2_obj, ....], }
        self.cameras['pmv'] = { 'obj' :self.VIEWER.cameras[0],
                                'structures' : [],
                              }
        self.cameraslist = ['pmv']    # name0, name1, name2 
                                      # keep the order in which cameras are added
        self.target = target
        print "        [ DONE ]"
        print "==========================================\n"
        self.initStyles()
        if self.target:
            self.addCamera(target = self.targer, name=name)

    def initStyles(self):
        """ initialize styles dictionary """
        #color_cb = CallbackFunction(self.mv.colorByAtomType, (['lines', 'balls', 'sticks'], log=0) )

        #self.styles  ={ 'default' : [ color_cb ] }
        # XXX WHAT TO DO?
        pass


    def togglepmv(self, event=None):
        """ toggle between visible and hidden pmv"""
        if self._pmv_visible:
            self._hidePmv()
        else:
            self._showPmv()

    def _showPmv(self, event=None):
        """ stop all cams and restore the underlying
            pmv session
        """
        if self.debug:
            print "_showPmv> called"
            print "ACTIVE CAMS", self.activeCams()
        self._pmv_suspended_cams = self.activeCams()
        self.activateCam(['pmv'], only=1, mols=True)
        self._pmv_visible = True
        self.mv.GUI.ROOT.deiconify()
    
    def _hidePmv(self, event=None):
        """ stop Pmv camera, minimize Pmv and
            restore previously disabled cams
        """
        self.VIEWER.cameras[0].suspendRedraw = 1 # stop updating the main Pmv camera
        self._pmv_visible = False
        self.mv.GUI.ROOT.withdraw()
        self.activateCam(self._pmv_suspended_cams, only=1, mols=True)

    def addCamera(self,target,name = '', depth=True, bgcolor=(0., 0., 0.)):
        """ add a new camera 'name' bound to 'target'"""
        if self.debug: print "adding another camera"
        if name in self.cameraslist:
            print "Camera [%s] already exist!", name
            return
        cam_obj = self.VIEWER.AddCamera(master=target)       # the next ones will be added)
        if depth:
            cam_obj.fog.Set(enabled=1)
        cam_obj.backgroundColor = ( bgcolor + (1.0,) )
        cam_obj.Redraw()

        self.cameraslist.append(name)
        self.cameras[name] = { 'obj':cam_obj, 'structures' : [] }
        return cam_obj


    def delCamera(self, idx=None, name=None, mols=True):
        """ delete camera by index or by name; by default all molecules
            loaded in a given camera are loaded
        """
        if self.debug: print "delcamera", idx, name
        if idx == None and name == None:
            print "delete camera by name or by idx!"
            return
        if idx == 0 or len(self.VIEWER.cameras) == 1:
            print "cowardly refusing to delete the main Pmv camera...(returning)"
            return
        self.VIEWER.DeleteCamera(idx)
        name = self.cameraslist.pop(idx)
        if mols:
            for s in self.cameras[name]['structures']:
                self.mv.deleteMol(s)
        # delete all objects from this camera
        self.nukeCamMols(name)
        # delete camera
        del self.cameras[name]

 
    def activeCams(self):
        """ return list of active cameras"""
        active = []
        #active = [ name for name in self.cameras.keys() if self.cameras[name]['obj'].suspendRedraw == 0 ]
        for c in self.cameras.keys():
            if not self.cameras[c]['obj'].suspendRedraw:
                active.append(c)
        return active

    def cams(self):
        """ return the list of all camera names"""
        return self.cameras.keys()
        
    def cameraByName(self, name): #, attribute='obj'):
        """ retrieve camera object by name
            None, if camera doesn't exist
        """
        cam = self.cameras.get(name, None)
        if not cam == None:
            return cam['obj']
        else:
            return None

    def cameraStructures(self, name):
        """ return all mols loaded in this camera"""
        return self.cameras[name]['structures']

    def activateCam(self, namelist=[], only=1, mols=True):
        """ activate redraw on selected camera and disabling 
            (by default) other cameras
        """
        # - reactivate this camera
        if self.debug: print "activatecam> namelist", namelist
        for c in self.cameras.keys():
            if c in namelist:
                for s in self.cameras[c]['structures']:
                    # XXX ASK MICHEL
                    if isinstance(s, Molecule):
                        s = s.geomContainer.geoms['master']
                    s.Set(visible=True) #,redraw=False)
                self.cameras[c]['obj'].Redraw()
                self.cameras[c]['obj'].suspendRedraw = 0
            elif only:
                self.cameras[c]['obj'].suspendRedraw = 1
                # hide molecules loaded in this camera
                for s in self.cameras[c]['structures']:
                    if isinstance(s, Molecule):
                        s = s.geomContainer.geoms['master']
                    s.Set(visible=False) #,redraw=False)

    def deactivateCam(self, namelist=[]):
        """ disable redraw update in cameras"""
        self.VIEWER.redrawLock.acquire()
        if len(namelist) == 0:
            namelist = self.cameras.keys()
        for c in namelist:
            self.cameras[c]['obj'].suspendRedraw = 1
        self.VIEWER.redrawLock.release()


    

    def loadMolWithStyle(self, molfile, style='default'):
        """ load molecules with representation style 
        """
        mol = self.mv.readMolecule(molfile,  modelsAs='conformations')
        return mol


    def loadInCamera(self, molfile, camera, style='default'):
        """ load molecule in selected camera
            and apply optional repr.style
        """
        mol = self.loadMolWithStyle(molfile, style=style)[0]
        self.cameras[camera]['structures'].append(mol)
        return mol

    def deleteInCamera(self, molobj, camera):
        """ delete an object from a camera"""
        m = """
#######################################
###
###
### PROBLEMATIC DELETION! ASK MICHEL
### ISSUE WITH DELETING FILES
###
###
#######################################"""
        #print m
        #print "LIST OF STRUCTURES", self.cameras[camera]['structures']
        self.mv.deleteMol(molobj)
        self.cameras[camera]['structures'] = [ x for x in self.cameras[camera]['structures'] if not x == molobj ]
        return
        idx = self.cameras[camera]['structures'].index(molobj)
        d = self.cameras[camera]['structures'].pop(idx)
        try:
            self.mv.deleteMol(d)
        except:
            print "TRYING TO DELETE MOLECULE %s RAISED ERROR!" % d


    def nukeCamMols(self, camera):
        """ delete all molecules from a cam"""
        for m in self.cameras[camera]['structures']:
            self.mv.deleteMol(m)
        self.cameras[camera]['structures'] = []


    def centerView(self, item=None):
        """ center the view on specified target
            if target is None, reset the view
            on all mols
        """
        root = self.VIEWER.rootObject
        if item == None:
            item = root

        self.VIEWER.toggleTransformRootOnly(False)
        self.VIEWER.SetCurrentObject(item)
        #self.VIEWER.Reset_cb()
        self.VIEWER.Normalize_cb()
        self.VIEWER.toggleTransformRootOnly(True)
        self.VIEWER.Center_cb()
        self.VIEWER.SetCurrentObject(root)


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
    #root.mainloop()

