# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 19:16:40 2013

@author: Ludovic Autin
"""
import shutil
import os,sys
from time import time
try :
    import urllib.request as urllib# , urllib.parse, urllib.error
except :
    import urllib
import json
#import upy

def checkURL(URL):
    try :
        response = urllib.urlopen(URL)
    except :
        return False
    return response.code != 404
    
class Updater:
    def __init__(self,*args,**kw):
        self.list_host=["all","maya","c4d","blender","3dsmax"]        
        self.host="all"
        if "host" in kw :
            self.host=kw["host"]
            if self.host not in self.list_host:
                self.host = "all"
        self.liste_plugin={"epmv":{},"autopack":{},"upy":{}}
        if "liste_plugin" in kw :
            self.liste_plugin = kw["liste_plugin"]
        self.helper=None
        if "helper" in kw :
            self.helper=kw["helper"]
#        else :
#            self.helper = upy.getHelperClass()()
        self.gui = None
        if "gui" in kw:
            self.gui = kw["gui"]
        self.server = "https://upy.googlecode.com/svn/branches/updates/"#could be google
        self.url = self.server+"update_notes_"+self.host+".json"
        self.local_path = "/Users/ludo/DEV/upy_google_svn/branches/updates"
        self.result_json={}
        self.update_notes=""
        self.typeUpdate="std"
        if "typeUpdate" in kw :
            self.typeUpdate=kw["typeUpdate"]
        
    def checkForUpdate(self,):
        #check on web if update available
        #return boolean for update_PMV,update_ePMV and update_pyubics
        #where to check and what type dev/stable/host
        self.new_version = self.liste_plugin
        self.update_notes = ""
        self.result_json=None
        #need version
        URI=self.url
        tmpFileName = "update_notes_"+self.host+".json"
#        if not os.path.isfile(tmpFileName):
        urllib.urlcleanup()
        if checkURL(URI) :
            urllib.urlretrieve(URI, tmpFileName)#,reporthook=self.helper.reporthook)
            #geturl(URI, tmpFileName)
        else :
            print ("problem connecting to server")
            return None
        with open(tmpFileName, 'r') as fp :#doesnt work with symbol link ?
            self.result_json=json.load(fp)
        do_update=[]
        for plug in self.liste_plugin:
            self.liste_plugin[plug]["update"]=False
            if self.liste_plugin[plug]["version_current"] != self.result_json[plug]["version_"+self.typeUpdate]:
                if self.result_json[plug]["host"] == ["all"] or self.host in self.result_json[plug]["host"]:
                    self.liste_plugin[plug]["update"]=True
            self.liste_plugin[plug]["host"] = self.result_json[plug]["host"]
            do_update.append(self.liste_plugin[plug]["update"])
        self.update_notes=self.result_json["notes"]
        #self.merge_list_plug()
        print(self.update_notes)
        os.remove(tmpFileName)
        return do_update        

    def update(self,backup=False):
        #path should be set up before getting here
        for plug in self.liste_plugin:
            if plug == "notes":
                continue
            if self.liste_plugin[plug]["update"] :
                print ("update "+plug+" "+str(backup))
                self.update_plug(plug,typeUpdate=self.typeUpdate,backup=backup)

    def checkUpdate_cb_cb(self,res):
        self.gui.drawMessage(title='update',message="The plugins will now update. Please be patient while the update downloads. This may take several minutes depending on your connection speed.")
        self.update(backup=res)
        self.gui.drawMessage(title='update',message="You are now up to date. Please restart "+self.host)
        self.helper.resetProgressBar()
            
    def checkUpdate_cb(self,res):
        if res :
            self.gui.drawQuestion(question="Do you want to backup the current version?",callback=self.checkUpdate_cb_cb)

    def checkUpdate(self,*args):
        doit=self.checkForUpdate()
        if self.gui is None :
            return
        if True in doit :
            #need some display?
            msg = "An update is available.\n"
#            msg+= self.epmv.inst.update_notes
            msg+= "Do you want to update?\n"
            self.gui.drawQuestion(question=msg,callback=self.checkUpdate_cb)
        else :
            self.gui.drawMessage(title='update',message="You are up to date! No update necessary.")
            
    def update_plug(self,plug,path=None,typeUpdate="std",backup=False):
        import zipfile
        p = path
        if p is None:
            p = self.liste_plugin[plug]["path"]#AutoFill.__path__[0]+os.sep #path of plug      
#        print "update_AF",AFwrkDir1
        if self.host in self.result_json[plug]["host"] :
            URI=self.server+"/"+plug+"_"+typeUpdate+"_"+self.host+".zip"
        else :
            URI=self.server+"/"+plug+"_"+typeUpdate+"_all.zip"
        os.chdir(p)
        os.chdir("../")
        patchpath = os.path.abspath(os.curdir)
        tmpFileName = patchpath+os.sep+plug+"_"+typeUpdate+".zip"
        
        urllib.urlcleanup()
        if checkURL(URI) :
            urllib.urlretrieve(URI, tmpFileName,reporthook=self.helper.reporthook)
        else :
            return False
        zfile = zipfile.ZipFile(tmpFileName)
#        TF=tarfile.TarFile(tmpFileName)
        dirname1=p#+os.sep+".."+os.sep+"AutoFill"
        import shutil
        if backup :
            #rename AF to AFv
            dirname2=dirname1+self.liste_plugin[plug]["version_current"]#the version
            print(dirname1,dirname2)
            if os.path.exists(dirname2):
                shutil.rmtree(dirname2,True)
            shutil.copytree(dirname1, dirname2)
        if os.path.exists(dirname1):
            shutil.rmtree(dirname1,True)           
#        TF.extractall(patchpath)
        zfile.extractall(patchpath)
        zfile.close()
        os.remove(tmpFileName)
        return True
        
    def writeUpdateNote(self,filename=None,notes=""):#std or dev
        result_json={}
        for plug in self.liste_plugin:
            result_json[plug]={}
            if "version_std" in self.liste_plugin[plug] :
                result_json[plug]["version_std"]=self.liste_plugin[plug]["version_std"]
            if "version_dev" in self.liste_plugin[plug] :
                result_json[plug]["version_dev"]=self.liste_plugin[plug]["version_dev"]
            result_json[plug]["host"]=self.liste_plugin[plug]["host"]
        result_json["notes"]=notes
        f="update_notes_"+self.host+".json"
        if filename is not None:
            f=filename
        with open(f, 'w') as fp :
            json.dump(result_json,fp,indent=4, separators=(',', ': '))#,indent=4, separators=(',', ': ')
        
    def readUpdateNote(self,):
        URI=self.url
        tmpFileName = "update_notes_"+self.host+".json"
        urllib.urlcleanup()
        if checkURL(URI) :
            urllib.urlretrieve(URI, tmpFileName)#,reporthook=self.helper.reporthook)
            #geturl(URI, tmpFileName)
        else :
            print ("problem connecting to server")
            return None
        with open(tmpFileName, 'r') as fp :#doesnt work with symbol link ?
            self.result_json=json.load(fp)

    def merge_list_plug(self):
        for plug in self.result_json :
            if plug == "notes":
                continue
            if plug not in self.liste_plugin :
                self.liste_plugin[plug]=self.result_json[plug]
            else :
                for opt in self.result_json[plug]:
                    if opt not in self.liste_plugin[plug]:  
                        self.liste_plugin[plug][opt]=self.result_json[plug][opt]
                if self.liste_plugin[plug]["version_dev"] < self.liste_plugin[plug]["version_std"]:
                    self.liste_plugin[plug]["version_dev"] = self.liste_plugin[plug]["version_std"]

    def update_svn_export(self,host=None):
        if host is None:
            host=self.host
        for plug in self.liste_plugin:
             self.update_svn_export_one_plug(plug,host)   
             
    def update_svn_export_one_plug(self,plug,host):
        d = self.liste_plugin[plug]["path"] #"/usr/local/www/projects/ePMV/SOURCES/export/ePMV"
        if os.path.exists(d):
            shutil.rmtree(d)            
        os.system("svn export "+self.liste_plugin[plug]["svn"]+" "+self.liste_plugin[plug]["path"]+" > "+self.liste_plugin[plug]["path"]+"log")
        os.system("tail -1 "+self.liste_plugin[plug]["path"]+"log > "+self.liste_plugin[plug]["path"]+"version")
        f = open(self.liste_plugin[plug]["path"]+"version","r")
        lines = f.readline().split(" ")
        lines = lines[-1][:-2].replace(" ","")
        f.close()
        f=open(self.liste_plugin[plug]["path"]+os.sep+"version.txt","w")
        f.write(self.liste_plugin[plug]["major"]+"."+lines)
        f.close()
        self.liste_plugin[plug]["version_"+self.typeUpdate] = self.liste_plugin[plug]["major"]+"."+lines
        self.liste_plugin[plug]["host"] = host
        for h in host :
            f=self.local_path+os.sep+plug+"_"+self.typeUpdate+"_"+h+".zip"
            if os.path.isfile(f) :
                os.remove(f)
            os.system("cd "+d+"/..;zip -r "+f+" "+plug+"/  >logx")
    
if __name__ == "__main__":  
#    set afversion=`svn info https://subversion.assembla.com/svn/autofill/trunk/AutoFillClean | grep "Revision:" | cut -d: -f2 `
#    set epmvversion=`svn info https://subversion.assembla.com/svn/epmv/trunk/ | grep "Revision:" | cut -d: -f2 `
#    set upyversion=`svn info https://subversion.assembla.com/svn/upy/trunk/upy | grep "Revision:" | cut -d: -f2 `
    do_json=False
    do_update=True
    if do_json : 
        liste_plugin={"upy":{"version_current":"0.6.381","version_std":"0.6.381","version_dev":"0.6.381","host":["all"]},
                      "AutoFill":{"version_current":"0.5.639","version_std":"0.5.639","version_dev":"0.5.639","host":["all"]},
                        "ePMV":{"version_current":"0.5.151","version_std":"0.5.151","version_dev":"0.5.151","host":["all"]}}
        #from upy.upy_updater import Updater
        up = Updater(host=["all"],liste_plugin=liste_plugin)
        up.writeUpdateNote(notes="blabla")
    if do_update:
        liste_plugin={"upy":{"path":"/Users/ludo/DEV/upy_google_svn/branches/updates/upy","svn":"https://subversion.assembla.com/svn/upy/trunk/upy","major":"0.6"},
                      "AutoFill":{"path":"/Users/ludo/DEV/upy_google_svn/branches/updates/AutoFill","svn":"https://subversion.assembla.com/svn/autofill/trunk/AutoFillClean","major":"0.5"},
                        "ePMV":{"path":"/Users/ludo/DEV/upy_google_svn/branches/updates/ePMV","svn":"https://subversion.assembla.com/svn/epmv/trunk/","major":"0.5"}}
        #from upy.upy_updater import Updater
        up = Updater(host=["all"],liste_plugin=liste_plugin,typeUpdate="std")
        up.update_svn_export(host=up.list_host)
#        up.readUpdateNote()
#        up.merge_list_plug()
#        up.writeUpdateNote(filename="/Users/ludo/DEV/upy_googlesvn/branches/updates/update_notes_all.json",notes="new update systems")
        up = Updater(host=["all"],liste_plugin=liste_plugin,typeUpdate="dev")
        up.update_svn_export(host=up.list_host)
        up.readUpdateNote()
        up.merge_list_plug()
        for name in up.list_host:
            up.writeUpdateNote(filename="/Users/ludo/DEV/upy_google_svn/branches/updates/update_notes_"+name+".json",notes="new update systems")
        #for host specific 
#        up = Updater(host=["maya"],liste_plugin=liste_plugin,typeUpdate="std")
#        up.update_svn_export()
        #this willl create an update just for maya
        #so shoul we have udpate_note per host
        #commit the change ?
        #upload the zip to google ? =>stable?
        
        