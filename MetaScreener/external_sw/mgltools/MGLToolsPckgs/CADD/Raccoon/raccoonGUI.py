
#!/usr/bin/env python
#
# Raccoon
#
# Tk Virtual Screening Interface for AutoDock
#
# v.1.1.0  Stefano Forli
#
# day_1: Monday, February 6 2012
# day_2: Monday, February 13 2012
# day_3: Tuesday, February 14 2012
# day_4: Wednesday, February 15 2012


# Copyright 2012, Molecular Graphics Lab
#     The Scripps Research Institute
#        _  
#       (,)  T  h e
#      _/
#     (.)    S  c r i p p s
#      '\_
#       (,)  R  e s e a r c h
#      ./'
#     ( )    I  n s t i t u t e
#      "
#
#
#     This program is free software: you can redistribute it and/or modify
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#
#################################################################
#
# Hofstadter's Law: It always takes longer than you expect,
#                   even when you take Hofstadter's Law 
#                   into account.
#
#    The Guide is definitive. Reality is frequently inaccurate.
#        Douglas Adams 
#
#################################################################
#

# XXX DEBUG
from time import sleep
#


from raccoon import Raccoon
import Pmw
from PmwOptionMenu import OptionMenu as OptionMenuFix
import operator
import platform # system, platform.uname()
from tkMessageBox import *
from tkFileDialog import *
from Tkinter import *
import tkSimpleDialog as tks
import shutil
import tkFont
import ImageTk
#from TkTreectrl import *
import TkTreectrl
import os, time, datetime
from dateutil import parser
from mglutil.util.callback import CallbackFunction
from HelperFunctionsN3P import *
import HelperFunctionsN3P as hf
from mglutil.util.packageFilePath import getResourceFolderWithVersion
from EmbeddedCamera import *
import raccoonGUI_PrjManagerTree
import raccoonGUI_ResManagerTree
#from VinaScreening import *
#from VinaScreeningOpalRacc import *
from raccoonGUI_PrjManagerTree import VirtualScreening, Experiment, Project, Research

# -- OPAL CLIENT
import OpalClient
#from AppService_client import AppServiceLocator, getAppMetadataRequest, \
from CADD.Raccoon.AppService_client import AppServiceLocator, getAppMetadataRequest, \
      launchJobRequest, getOutputsRequest, queryStatusRequest, destroyRequest
#from AppService_types import ns0
from CADD.Raccoon.AppService_types import ns0
# -- OPAL CLIENT /end



from sys import exc_info, argv
import urllib


OPAL_HISTORY="raccoon_opal.hist"
OPAL_SERVERS="raccoon_opal_servers.conf"
OPAL_CONFIG='raccoon_opal.conf'
RESULTS_LOCATION='results'
MAX_RESULTS=100

class RaccoonOpalGUI(Raccoon):

    def __init__(self, root=None, debug=False, mode='vina', local_testing=False):

        # XXX TODO 
        # the entire session config must become a single dict
        # so entries like self.OPAL_useremail will be keys...
        #

        """ from mglutil.splashregister.splashscreen import SplashScreen
            from mglutil.splashregister.about import About
        about = About( image_dir='/entropia/local/rc3/MGLToolsPckgs/Pmv/Icons/Images/', third_party='Luca Code', path_data='.', title="TESTING", version='1.0', revision='a', copyright='TSRI+SF', authors='SF, MS, AO', icon=None)
        splash =  SplashScreen(about, noSplash=noSplash)
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        NameError: name 'noSplash' is not defined
        splash =  SplashScreen(about, noSplash=False)
        splash.finish()
        from __init__.py in pkgs/Pmv
        """

        # get the root
        self.root = root
        self.debug = debug
        if self.debug:
            print "LAUNCHED IN DEBUG MODE"
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        # initialize Raccoon
        Raccoon.__init__(self, mode = mode , debug = debug)
        self.setBoxCenter([0., 0., 0.])
        self.setBoxSize([0., 0., 0.])
        self.MAX_RESULTS = MAX_RESULTS

        self.local_testing=local_testing

        # paths and config files
        self.initRaccoonFiles() # initialize 
        #print self.gridBox()

        self.initOpalStuff()

        self.makeRaccoonGUI(root=root)

        # populate the multilist widget jobs history
        self.initJobsHistoryContainer()

        # read the default configuration
        try:
            self.readRaccoonOpalConfig()
            #self.OPAL_useremail = StringVar(value=self.def_label_value)
            self.updateStatus()
        except:
            if self.debug: print "NO RACCOON CONF FILE PRESENT!"
            pass

        # variables here
        print "\n\n[ RACCOON READY ]"

    def initRaccoonFiles(self):
        self.mglroot = getResourceFolderWithVersion()
        self.racroot = self.mglroot + os.sep + 'Raccoon'
        self.OPAL_HISTORY = self.racroot+os.sep+OPAL_HISTORY
        self.OPAL_SERVERS = self.racroot+os.sep+OPAL_SERVERS
        self.OPAL_CONFIG  = self.racroot+os.sep+OPAL_CONFIG
        self.RESULTS_LOCATION = self.racroot+os.sep+RESULTS_LOCATION
        from CADD.Raccoon import ICONPATH, RESULTFILE, RACPATH
        self.ICONPATH = ICONPATH
        self.RESULTFILE = RESULTFILE
        self.RACPATH = RACPATH
        if not os.path.exists(self.racroot):
            if self.debug: print "__init__> creating a new Raccoon directory"
            os.makedirs(self.racroot, 0755) 
        
        if not os.path.exists(self.RESULTS_LOCATION):
            if self.debug: print "__init__> creating a new Raccoon results directory"
            os.makedirs(self.RESULTS_LOCATION, 0755) 
            
        for f in self.OPAL_HISTORY,  self.OPAL_SERVERS, self.OPAL_CONFIG:
            if not os.path.exists(f):
                open(f, 'w').close()




    def initJobsHistoryContainer(self):
        #data = self.readJobsStatusFile()
        #if data:
        #    self.populateJobsHistoryContainer(status_list = data)
        #else:
        #    print "NO DATA SO FAR!"
        self.jobManTree.setDataFile(self.OPAL_HISTORY)

    def parseRaccoonOpalConfig(self, fname=None):
        if fname == None:
            fname = self.OPAL_CONFIG
        try:
            conf = getLines(self.OPAL_CONFIG, doStrip=1)
            conf_parsed = {}
            for l in conf:
                kw, val = l.split("=")
                val = val.strip()
                kw = kw.strip()
                conf_parsed[kw] = val
            return conf_parsed
        except:
            return {}

    def readRaccoonOpalConfig(self):
        if self.debug: print "initializing config..."
        conf_parsed = self.parseRaccoonOpalConfig()
        for kw in conf_parsed.keys():
            if kw == 'default_email':
                self.OPAL_useremail.set( conf_parsed[kw])
            elif kw == 'results_location':
                self.RESULTS_LOCATION = conf_parsed[kw]
                # XXX trigger an update of the job manager?
            elif kw == 'max_results':
                self.MAX_RESULTS = int(conf_parsed[kw])

    def writeRaccoonOpalConfig(self, fname = None, values={}):
        if fname == None:
            fname = self.OPAL_CONFIG
        if self.debug: print "DATA", fname, values
        if values == {}:
            if self.debug: print "writeRaccoonOpalConfig> a dict of values is necessary!"
            return
        conf_parsed = self.parseRaccoonOpalConfig()
        for kw in values.keys():
            conf_parsed[kw] = values[kw]
        fp = open(fname, 'w')
        for kw in conf_parsed.keys():
            text = "%s = %s\n" % (kw, conf_parsed[kw])    
            fp.write(text)
        fp.close()

    def readJobsStatusFile(self, fname = None):
        
        #self.jobManTree.listbox.config(bg='white',fg='black',font=self.FONT,
        #    columns=('job name', 'date', 'server', 'status','ID','results URL'),
        
        def _clean(word): # XXX OBSOLETE?
            """ remove the heading/trailing quotes """
            if word[0] in ['"', "'"]:
                word = word[1:]
            if word[-1] in ['"', "'"]:
                word = word[:-1]
            return word
        if fname == None:
            fname = self.OPAL_HISTORY
        data = getLines(fname, doStrip=1, removeEmpty=1)
        status_list = []
        for i in range(len(data)):
            status_list.append( map(_clean, data[i].split('\t')) )

        return status_list

    def writeJobsStatusFile(self,  infolist=[], fname = None, mode = 'w'):
        # XXX THIS Should handle the deletion of jobs
        if fname == None:
            fname = self.OPAL_HISTORY
        fp = open(fname, mode = mode)
        for jobInfo in infolist:
            jobinfostr = map(lambda x : "\"%s\"" % x, jobInfo)
            print "JOBINFOSTR IS>", jobinfostr
            jobinfostr = "\t".join(jobinfostr)
            fp.write(jobinfostr+'\n')
        fp.close()
        
    def readJobStatusFile(self, fname = None):
        if fname == None:
            fname = self.OPAL_HISTORY
        data = hf.getLines(fname, doStrip=1)
        status = []
        for line in data:
            status.append( [ l.strip()[1:-1] for l in line.split('\t') ] )
        return status

    def updateJobDataFile(self, jobdata = [], fname=None):
        """ gets a list of jobdata [prj, exp, vs, vs.url... reslocation ]
            and update the history file
        """
        if fname == None: fname = self.OPAL_HISTORY
        status = self.readJobStatusFile()
        prj = jobdata[0]
        exp = jobdata[1]
        vs  = jobdata[2]
        found = False
        for i in range(len(status)):
            item = status[i]
            if item[0] == prj:
                if item[1] == exp:
                    if item[2] == vs:
                        status[i] == jobdata
                        found = True
                        break
        if not found: status.append(jobdata)
        self.writeJobsStatusFile(jobdata, mode='a')

    def updateJobsHistoryFile(self, fname = None):
        status = self.retrieveJobsHistoryContainer()
        self.writeJobsStatusFile(status)


    def retrieveJobsHistoryContainer(self):
        info = self.jobManTree.getTreeGraph(useName=False)
        #st_format = """'%s'\t'%s'\t'%s'\t'%s'\t'%s'\t'%s'\t'%s'\t'%s'"""
        status = []

        for prj in info:
            for exp in prj.children:
                for vs in exp.children:
                    resout = vs.properties['results_location']
                    if not resout == '':
                        status.append( [prj.name, exp.name, vs.name, vs.date, vs.url, vs.status, vs.jobId, vs.resurl, resout])
                    else:
                        status.append( [prj.name, exp.name, vs.name, vs.date, vs.url, vs.status, vs.jobId, vs.resurl])
        # the sorting by date should happen here...
        status.sort(key=lambda d: parser.parse(d[3]) )
        if self.debug:
            print "DEBUG retrieveJobsHistoryContainer"
            for i in status: print i
            print "DEBUG retrieveJobsHistoryContainer"
        return status


    def populateJobsHistoryContainer(self, status_list = []):
        if len(status_list):
            self.JobManagerTree.setDataFile()
            #    self.jobManTree.listbox.insert('end', info[0], info[1], info[2], info[3], info[4], info[5])

    
    def initOpalStuff(self):
        # list of servers providing OPAL docking services
        self.OPAL_servers_list = []
        # job status
        self.OPAL_jobstatus_table = { 8 : 'Successful', 
                                    2 : 'Running...',
                                    4 : 'Killed/Error',
                                    1 : 'Submitted',
                                 }

        try:
            self.OPAL_servers_list +=  getLines(self.OPAL_SERVERS, doStrip=1)
            if self.debug: print "GOT LIST OF SERVERS FROM FILE", self.OPAL_SERVERS
        except:
            print "PROBLEM READING SERVER LIST", self.OPAL_SERVERS


        # ligand libraries
        self.OPAL_ligLib = []
        self.OPALurl = StringVar()
        self.initOPALserver()



    def initOPALserver(self):
        url = self.OPALurl.get()
        self.url = url
        if url == '':
            return
        if self.debug: print "initOPALserver> init the url to", url
        # initialize the server connection
        self.OpalService = OpalClient.OpalService(url)



    def makeIcons(self):
        icon_open_file='''\
        R0lGODlhFgAWAPYAAEt0R0x2SVF7SVZ+SVmDSV+ISmaOTWiPSmiQSWqRS22USmuSTWyUT3SaTG6V
        UHCYUlumVHqgT2CpVmWrV2ywWnW1Xna1Xn25YH+7YXy6Y326Y4CmUYesVImtVoqvWY2wXI+yXpC0
        X4a9Y4G7ZIO9ZYO9Zoe+ZYS/Z4W/Z4m/Z5W4ZJi6ZIrBaIzCaI7DaYzBaozCa4/Fa43DbJ/AZ5HG
        bZLHbpTGbJPIb5TIcZXJcZvKdZzMdJ3NdaTFaanKaq7NarHRabLRabLSa7PTbaLOfqTReaTReqrW
        favWfqjShq7UjbLagbnehbrfhrPYlb/hh8HjisjmlNXsqwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5
        BAEAAFMALAAAAAAWABYAAAfegFOCg4SFhoeIiYdBQkNDQkCKhj9RUlJRP5KFPk9QUE8+moQ9TE1N
        TD2igzNLrUszqoIrR0hIRyuKHB0eHyAhKkVGRkUqISAfHh0chBs2OkRJSk47PDw7TkpJRDo2G4QR
        LS4xNDU3ODk5ODc1NDEuLRGEDSImKSwvMDL6MjAvLCkmRDQgpOAChhEkSpxAwRDFiRIkRmC4oIAQ
        ggMJFjBw8CCDBg0ZHjhgsCDBAQSKDFSwYKGCgVhTClCYSaEATAITck4gAHOAhJ8SBsAUAKEoBAEw
        AQRYGgAAzKdQpwQCADs=
        '''
        self.ICON_open_file = PhotoImage(data=icon_open_file)

        icon_open_dir ='''\
        R0lGODlhFgAWAPcAAHpLGUhgSEtkS1d3VVl3V299T2d8UZxhH5tiIZxhIKJnJaZrKqpwL7B1NbV6
        Obp/P89/KVqdUlybVGOAU2GHVGuOVm2PV3STW3yaWn2aWmioVnWpWtSCKdaHMdaHMteIM9iMOtiO
        PNqPPduQP4CSVqGIQr+EQ4emXJKkWoO6X5SzX6KvW7moXI+9Ypa1YKq2YcCFRMSJScmOT9uRQNuR
        QdmRQtuURtyVSN2XSdqWTNuWTN2XTN+ZTd2ZT86UU8+VVN6bUtybVN+dVN6dVtSaWeGfVt+hXuKg
        WOOhWeOiWeCgWuGiXd6jYtujZNyjZN6lZt+mZ8WzYMm4Z+GjYuSlYOWmYuCjZOOmZuWoZOaoZOap
        ZeepZuKnaeCoauGoa+aoaOOrbuSqbOerbOSsb+etbuitbumvb+WuceaucOStcuStc+avcumvcOex
        deawduawd+mwc+qwcuuxcuqyduazfOizeum0eey0ee22e+q1fOq1feu3fei3f+64fe64fqTAY6TA
        ZK/CY6jHY7DDZKHQaa3Ta7LabpG+hOi3hOq5g+y5gO25gO67g+28hu+9hu+/ivC/iPG/iuu/kJzF
        ibLWkr/gmLjVq/HBjevAkO7FmfLEkPTGk/XHlfHLoPTPqPbUsPjZtvrcvcnis8TExMbGxsfHx8jI
        yMnJycvLy/vgw+vr6/Dw8PHx8fPz8/T09PX19fj4+Pn5+f39/QAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAALMALAAAAAAWABYA
        AAj+AGcJHEiwoMGDCBMqXMiw4axTpiJGPNWwFClUsDJmREWqo8eOpQiOekWypMmTr0YNZNLkSRcw
        Z9rY2bNo0R47bdaM8QLFiRWBRBBJytTJ0ydQoVKlCgXqk6dOmTAhIiLQBx0+iRo9uqRpEydOmzRd
        etQoER86PwTKUPOmjh5FjBxBihQJkiNGivLUcZNGhsAYXMKggTPnDp4+fvz0wXNnDhw0YbjEEGjC
        yJQrX8SUYRNHjpw4ZshIGSQoUBQYAh8EGaJkCZUqWbRs2aIFywtAhQwV+rNCoIMcOnoAEVLkCJIk
        SZCwcEGokqxKhFQIbFCjuo0bOHbw2M4DRQtKomJmiaLU4sQsBiDSgwghYsQMGjRmZEjBqpWrVqxS
        YJi1oIP//x58IOAHJGwwiSWrWDLJBhfMogAEHEQo4YQlWKDBIaocokEFE8wCwAEJhCjiiAgUQIEE
        EUhAgQEOCRTAAAQMIECLCQUEADs=
        '''
        self.ICON_open_dir = PhotoImage(data=icon_open_dir)

        self.ICON_email = ImageTk.PhotoImage(file=os.path.join(self.ICONPATH, 'message.png'))
        self.ICON_tree = ImageTk.PhotoImage(file=os.path.join(self.ICONPATH, 'tree.png'))



        icon_remove_sel ='''\
        R0lGODlhFgAWAPUAAIcoJIkpJpUxLKA4NMQ8NcU9NsY/OKxBOsdAOclCO8lDO7dIQclJQstMRs1P
        SMRSSs5STMhVTs9WT9BTTtFVT9FWT8pZUs1eVtFZU9RdVtBiW9VhWtdjXtJmX9hmYNpnYdRqY9dp
        ZNZsZtpoYtduaNp0cN5/euOIhOWSjuialuqhnuymogAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAACwALAAAAAAWABYAAAZ5QJZw
        SCwaj8ikcslsOp/QqPT4iFgumg5IRCKJQB3NxRJ5EBehkumESqlWK1UKdTKVQgviQYLJbDgeHyMj
        Hx4cGxkYEgdEAwwMDQ4QExQVFRQTEA4NjwNEAgShBQYICQoKCQgGBaEEAkQAAbKztLUBAFO5uru8
        vb69QQA7
        '''
        self.ICON_remove_sel = PhotoImage(data=icon_remove_sel)




        icon_remove_all ='''\
        R0lGODlhFgAWAPYAABISEh4eHiIiIiMjIyUlJSYmJiwsLDAwMDMzMzQ0NDU1NTY2Njs7Ozw8PD09
        PT8/P0BAQEFBQUREREVFRUdHR0hISEpKSkxMTE5OTk9PT1BQUFFRUVRUVFVVVVhYWFlZWVtbW11d
        XV9fX2BgYGFhYWJiYmNjY2VlZWZmZmdnZ2hoaGlpaWpqamxsbG1tbW9vb3BwcHFxcXNzc3R0dHV1
        dXZ2dnd3d3h4eHt7e3x8fH19fX5+fn9/f4CAgIGBgYKCgoODg4SEhIWFhYqKiouLi4yMjI2NjY6O
        jo+Pj5CQkJGRkZKSkpOTk5SUlJWVlZaWlpeXl5iYmJmZmZubm56enp+fn6CgoKKioqOjo6Wlpaam
        pqenp6mpqaqqqqurq6ysrK2tra6urq+vr7CwsLGxsba2tr29vcDAwMHBwcPDw8bGxsfHx8jIyMrK
        ysvLy8zMzM3Nzc7Ozs/Pz9TU1NbW1tfX19jY2N3d3eHh4eLi4gAAAAAAAAAAAAAAAAAAAAAAACH5
        BAEAAHoALAAAAAAWABYAAAf+gHqCg4SFhodOSkZCNTVBR0lQh4IcOmBymHBoaG+YcmA6HIUROXNn
        XUkoEAUEDylKXWdzORGEEms5LTo6IxYIBxQlPDstO2sShA5AdHBtZVAwGxwyT2VucXQ/DYUkUmx5
        d3Z1mHR2d3hqTyKGCThWbm1mYVRUYGZtblU5CYYAGT5exlAhcuPGECpjwPzQAOBQBRhIuEzZIQhI
        Ey5RaFSYFCHGEi1RfAjqIeWLExkTJjHwiKUJEEE7pnxR8mLboQMujGSRQlFPDydblsQ4MGlACyNa
        oOAAMUIHkyxJXgiYFEAFEzFXjtyYUSQLGSUpph4yEGKJDxMbIlhYEeSJkxBFBjiGOBEDxAQEDTqk
        uLHCQ61DC2xkCTOEBYYLLIaEuTJDwSQ9H5CkQTOmSpUxaNIg+fBY0AIUOHoU7IEDxYLOqFOrJhQI
        ADs=
        '''
        self.ICON_remove_all = PhotoImage(data=icon_remove_all)


        icon_settings ='''\
        R0lGODlhFgAWAPcAACEnJywxMy40Ni81Ni80Ny41Ny81NzA1NzE2NzA2ODA3ODE3ODE2OTA3OTE3
        OTI4OjM4OjM5OjM4OzM5OzM6OzU6OzU6PDU7PDU7PTU8PTY8PDc8PDc8PTY8Pjc8Pjc9Pjs/Pzg+
        QDo/QTlAQDtAQj1BQzxCQz1DRD5ERj9ERktOSlBTT1VXU1ZYVFhbVlhbV1xeWmlranp9e3t+f32A
        gX+CgIaJhYqMiIuNiZCTkZCTkpOVkZWYlZaYlZmcl5mamJqcmpyempuenZ6enZ6gnJ+gnaChnqCi
        np+ioKKkoaGko6Kko6eppaqrqKmrqqyvqq2uq62vq66uq6uurKyvra6vrK6vra+wra6wrrO3sLO2
        sbO0s7O2tLa5tLi6tre5uLm7uL2+vrzAvL/BvsLGv8DCwcHCwcLCwcLEwcLGwMPGwMXFxMbHxcXK
        w8bIxMfIxsfJx8zMy8zNzM3OzM/PzsvQyc/SzdDSztHUz9DR0NLT0dLU0dPU0tXV09bX1dfX1tbY
        1NfZ1NfZ1tjc1tnc19na2Nvb2drc2Nvc2Nvd2tzc297e3d/f3t7g3N7i3N/h3uHh3+Hh4OLi4OPl
        4ufo5+jp5+nr6e3t7O7u7O7u7vf39/j4+Pv7+/z8+wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAJ4ALAAAAAAWABYA
        AAj+AD0J9NSCxQtPL1i0GMiwoUAWdCRdeXNFEh0WDjOyiLSpk6ZOmyJhzNjQhRRORWAU4STFBUmH
        azRhZKHpjCcTAiK89GQSpUpOPwSEkTNhYAOHGzt+3MTIQiFMKR4koKHkQkOIEtkkgeQEwpxLnDKV
        MWNIiIKGBQ8KwNBB0Z8jN4zoWQRmxksSX+DIyYMjSJMoR/hwWfAywZY+lI4wASJiCRotgh4wTIsQ
        xIMQlXyMOeEJRaIsjz4wkOAJ68SKcSb4eeJmSgkujdIggmIlQWmOHkFG0oDlTpdDlia1CSSGB5IN
        PE+mXFnDA5E9eNSQqUPITgYHAgbGnKlphA4mPag/AHI0yEuFksp/DqGQ40IAAxx22DhwFffSSCsK
        ABBIQEaM7AxhVQUbVVg0kkADCIBARgWp4IkKCu0k4YQUShgQADs=
        '''
        self.ICON_settings = PhotoImage(data=icon_settings)


        open_small_folder = (
        'R0lGODlhEAAQAPYAAJBZHp1iIaNoKKluLa5zM7V6Obp/P9ODKdSDKdWDKdeINdeJNdiKN9mPP8CF',
        'RMaLS9uSQtyTRN2VRt2VR9qUStuWS92YTsySUt+bUtybVNOYWN+eWeGcVOKeVuKeV+GiXNqgYtyj',
        'ZN+naeCiYuCjYuSkYOWnYuOnZeaoZeapZuaqaeOqbuOrbuetbeWuc+aucumwceqxc+uzc+myduiy',
        'd+azeuq1e+u1e+i1fu24fr+/v+y5gO66gey5gu+7g+m7huq7h+69hvDAivLCju3BlO7BlPPEkPDI',
        'nvHInvPPqPbVsvjausDAwMPDw8XFxcbGxsjIyPrfwvX19fj4+AAAAAAAAAAAAAAAAAAAAAAAAAAA',
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5',
        'BAEAAFQALAAAAAAQABAAAAfIgFSCg4SFg1BPiU9QhoNOUFORU1BNlZZOgkxSm5ydmzpUICEiKy40',
        'Njs7NjQuKyIhIBpARUhJSktRUUtKSUdEPxoXNTg9QUJDRkZDQkE9ODUXDywvMzc5PD4+PDk3My8s',
        'Dw4kJyotMDEyMjEwLSonIw4GGRsfJSYoKSkoJiUfGxkGClCoYAEDhw4ePHTggMFCBQoFCDSYCCGC',
        'hAkTJESAMLEBgQEKQipYwKAkgwUiFQwQgCCBy5cwESA4IABAgJs4c+YE0KgnlUAAOw==',
        )
        self.ICON_small_folder = PhotoImage(data=open_small_folder)


        default = (
        'R0lGODlhEAAQAPYAAIlyDotyDqCDEKGEEKSHFaSIFqiKFquNFbyaFLCSG7SVHrSXJ7aZJ72gMcin'
        'Ht+5HuK7HcaqPebBK+bBLOfBLefBLubEOebEOurHPOrIPcuvRM+zSs+1TdG2Tda7VNm+U9u+VNzB'
        'WNzCWd7CXN7CXevKSe3MS+7NTOrNUuzOXPDRV/HSWfHTWvHTW+HIZ+LJZuXMaubNbefPbebOb/HU'
        'YfPVZfTXZ/XXaPXYaejPcujQdurSefbcdffcdvjddvfdfPPchPHdkfjhgvrihPfhj/jjjPbimPfj'
        'm/LioAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5'
        'BAEAAEkALAAAAAAQABAAAAeLgEmCg4I5hIeHMjsyiI06RDqNhy9ARUAukh8hIzNCQ0IzJCIggxwe'
        'MEFHPz0+PTxGSDEeHYIbKTQ1Njc4NzY1NCkbhBooKissLSwrKigaiBElJifTJiURjQ0WGBncGBcN'
        'jQwSExQVFBMSC40JEA8OCg4PEAmNBwgGBEkFBggHjQIADgUYIKmgQUmBAAA7',
        )
        self.ICON_default = PhotoImage(data=default)



        no_go = (    
        'R0lGODlhMAAwAPcAAGITBH0mAHooA4MAAIwAAJMAAJsAAKQBAKwAAKUJAKoMAKMICLMAALsBALEL' 
        'AL0MAbgODqcUAKoSAKwcAKcZALIaAL8cALgUAKkTE6weHrYWFocnAIkrBJssDIwzA4gzB5U2A5c3' 
        'B5oqF446GJw+FawjAKMnBrIkALwkALMtAKM/Aaw8AKwyBrU0AL00ALo8ALQ5BKk2FLM3GKQtJrch' 
        'IbkoKLYyKqk0NL84OMMAAMsAAMAMAMIUAMUbAcMVEMYjAMgmAMUtAMosAMgrDss0AMY7A847ANA/' 
        'AMU5F8UoJMU2JcYzMsI+Pss7O8ozM5hMAaxCAKRJAKpJALdAALtCALRNAbxLALFMCKxdAb1UArZd' 
        'ALlYAKNJHrdQGLVkAL1lAYlCL55GIYREN5lMO51QP6tMLKREIK5TK7pVLLdXOLtqLqxvNrp0NsBD' 
        'AM1DAMJMAMlLANFDANNMAMVTAMtVAMVYActcAdZUANZaANlcANNNFs5eF9VbEsRiAc1kAMxtANRk' 
        'ANliANNsAN1rAMt0ANZzANx0ANt7ANBJKc9fJNZeJcZaNtNfMtFQP8JiNMdnOtRhPsBwNrtERL9N' 
        'TbNMTKhTSrZYQ65VUr9cWL1iQp5uY6p3Y6h2ZbR+aMlGRcNeRNNfSMNSUs1SUs1bW9JaWc1qTdFs' 
        'RNh0R8ZqUsdgVNNtXNNnUs50W9p3U957Vtp8XsdiYcpkY8tpadNkZNZsasp1Yt58Ydl0bN19bNd3' 
        'Y89zc9Rzc9l2dtx7edZ9ddyCAOKEALqDbLyEZL+QYbuJdMiWXtWaXsOIZ9+CbdSaYcKLds2BcNyC' 
        'dd2BeceRe+CFecWhf7GLht2Dg9+Jgt2MjNSHgM+ah9OcitySkt+cnOCGhOGKhOKPj+ORj+WcnOCW' 
        'lt6vi9alh8OknMuomdOrnNWkleOyitOvot22reWmpuinp+Osp+O3puqzs+O9vOu+vue1tdXCvubH' 
        'vefJxu7T0/Pc3O3l4/Lm5PXs5fXr6fnu7Pnw7vr39vz49v///wAAACH5BAEAAP8ALAAAAAAwADAA' 
        'AAj+AP8JHEiwoMGDCBMqXMiwocOEBCIWmEhxYsSHGP9FJDDRgMePHiluzKhwY8cFGSbF0lVtFyxJ' 
        'GUIWuEjSoMQCBjDEyvaup8+e8LCFWmDAIoGaAgdIzClrXbunUKO2g9cu29CiNDMuPVADm7qv6tKl' 
        'AzuWrFheGQ7MPIpRKc4DTL55m0u3rt261GionflwKQIm1LoJHkyYG7fChrlRy3vAQNaFHA0coCFN' 
        '2rRpz7Zp3rxNW2dt2qSFrhx6l4bGjxFGlAyBVi9msGM/mw27l23bvHbp3sWLVy9RCFCzRej2AAJP' 
        't5LXqraPXK1cyKIjw3WLOi1ZqebVkwVLFi1aSxD+YC1ZwDgEUqpUoVq2z5+/cqhQvULmytarV6pE' 
        'hXLnnh6mUKPMIkoD4qU20GrGObHKKp/Ugo97/vRzTSqmtOLKhaukYgk6EPpDDyWSiEKKBsHxddBq' 
        'CDDgCSifWHJPhxFak8Yjp5xiShppcAijOzcw4ckSDBQ4HEEESMaADysuUoYy/MDYjzNnqPEIGmXo' 
        '2OE9l8yAQxNNEKjWkEm95cADiDDCyCJmBANjhMpwYUYY56yZTyUz2LCEE0kwwMCXBnWEQAM8CKGH' 
        'Int0QUIn/ThJzAhxwpjPGCLYoEQSPuTQQJDjEfTWnzwYYYQcfBR6aJMd9jPPmvaQ0YEMSAzRww7+' 
        'DVxaYgEFvcVAAz8YEYccd+CBxxUfbJLomh0+ygEMRRAhRA88wHrpXgV5dMCtQOgqBx55BOKHFBxw' 
        'Miyx+YCxwQpueCoEEMw+4KVHRJaXYgNAHBFHr3kMYoggUgigCakw2iOGACrQcYcccRhx7quyFkWk' 
        'ZCk+IIS8vNZriCFbCABAPMRGA4AHWeSRxx1xFCzED7Du2djCxsVa7a54BDLIIH48IYA4xEbIiQBS' 
        '2BEIHiAboSwPsp5M0AHGMfBArp/ekQcgdkjxAc012+xBFX7kgQfBBvcQ9AEFGfdnAz0Q4ca8eNDh' 
        '9DhRQ9hPJyBU4SvIbggBdJBEd43Au4Ea4Yb+HG9AEQLaMOIDzbfu9RNM2wKHTMQOegbH9dBF3/pD' 
        'EUYUsUII5KyJzxpPDEN4hMJEYQUdcrgRhLpBilfr3Xo6YEEQLrDQAeAd4sMGFl5gUcya/QijghVw' 
        'uGFB43cfxLqeD6CQQgeZB66GF4T8QogXxXzezzErWFHEA3qmbnyQrV9QggnyBM6GFtH/Ir0XyXwe' 
        'DhRUoOBA43seVED3dzswQQkxlO8ePpHYgh8KcQhg/OIQhPiCMToEjipYwQXzAx8DEtK97klgfyw4' 
        'FT4cUYU6+EEQhZjYIQrxhz4YI1HgyIIV2lABBEQwSBC5FPEuWAIZsMMRVLDCHOwACEAI4of4JPSD' 
        'H5JhjjrMgQonOJ6eFvIn4iHggilIQQteQIU3vIEOduChEIWYRSO2IYmsi9XjFBIr/B1AARM4gRRf' 
        '0IYczuGNdqhDFt84Bxi0MIyXasgAcmCp1BHtgidowRSpkMM3WMGKhqRCChQQuQZYqi98lJXjEhCB' 
        'EpRAilOkIhVe0IIJRIBoKboVHzNSAD720XFEoyQFJkCBElCAAhFIACjfZUqk5EAHOigjKhvDS8nM' 
        '8lYNwGUDkCIQBuDSUpI0DtG8hkdc6gABxBzIHo+JzO69MFZ8FGY0DTKAYOrAlLEKZzZxOcFtQuRP' 
        'pkxnkAZgzna6853wjKdAAgIAOw==' )
        self.ICON_no_go = PhotoImage(data=no_go)

        go = (     
        'R0lGODlhMAAwAPYAAANDAwBNAAFUAQFcAQtUCwxdDRJfEgFkAgBrAQplCwlvCQBzAgF8AgxyDgZ6' 
        'CQt6DBlhGRdsGB1tHhR/FSJkIiNvIy1lLS1yLS58LzJvMjR0NDF8MTp8OkB9QAGEAwCKAgaHCAmE' 
        'CgeICgqMDQCTAACbAAifCAyHEAyOEhKIFRqPEQ6TEhGSFROTGRiWGxyaHgCkAACsAA2kDQCzAAG7' 
        'AQ+9DxOjExGsER+kHRqoGxC1EB6bIS2CLSyLLC2TLSycLDeENzKLMjyGPTyNPDeVNzScNDmSOT2c' 
        'PSSkJCSoJiekKSukKz6mJTOlMzCtMDukOzCyMDyxPADDAADLAAvDCwvLCwDTAAvUCwvcC0KDQkKJ' 
        'QkSTREObQ02XTUmaSVWUVVOeU0OlQ0WsRUykTEyqTEO6Q1m3SVSlVFOrU1ujW1usW1mwWWGeYmKu' 
        'YmykbGSyZGy1bHS0dHS6dHq9en/Bf4GngYPCg4nHiYvJi5PCk5PMk5rSmr7dvq3irQAAAAAAACH5' 
        'BAEAAH4ALAAAAAAwADAAAAf+gH6Cg4SFhoeIiYqLjI2Oj5CRkpOQFBmUmIUadQGZmQEFfASdnpMB' 
        'AX15FKelkad7enocrK2Op3p4eHpgtLWLAQJ4dnZ3eG6jvosCAnVzc3R0dXEQvcmFy3Ny2trOF9XW' 
        'ggIDcm9w5nDbWd/WAwNwb/Dw53FfyOCCAwdvavxram0A27wBY0AAKWsHELQhg6Yhv4f/0lQwCC7h' 
        'GjFjyGjUeKbjmTRpNgwQgHABmidhwojBGGaMS5dgwAgZmQwBAzJPcupMGcaLTy9dumhJQLMVggVi' 
        'nCxx0qTJkyZHokblsmWLFi0R2hllICaJkiVflzT5UaQIESJGhqjVkkWCVk/+CxhEwYGkbt0lP/L6' 
        '8BEkCJC/HDhUSJAAroMyUBJDYdpUr48eQXrw2EBZQwchGzItCAGjc+cSJEh8+BAixIMHDQ4cWAYA' 
        'gAU2XzSDiEHbcwnQHzwwYLAAwYGRBgs04AEXhI4ZtGN8Dp2bd+/f4hYcKMUABA0aM7Irh4Hbg24E' 
        'vhM0kN6qOhUpUrDXvp1bd28FD8iXH1EFfXrtt0W7n+BgQTIGI1wxxRTp0bBddyF40J81HgRohRXo' 
        'aQcDcyKkwBs4AGLxIIEGxpAfCydcCI4HK2jIIX4lvBACA/cIQmIVBN6nnAk7gMBii354wMJ51yEX' 
        'gwwu6IajiyvUgB1yMORIwAII/g3pxwctHFdbEih44OQgH7BwQ2cyKJHblViuYEMJNtRoJZiCQElX' 
        'CzaiiWULZqDwgZuFoMDEnHQSAoIKefbp55+AJhIIADs=' )
        self.ICON_go = PhotoImage(data=go)
        
        refresh = (     
        'R0lGODlhFgAWAPcAAARLAgZLAwFMAQFNAQBPAANOAQNMAgVNAwROAgdPAwZMBAdNBQhPBABQAAFQ' 
        'AAJQAQJRAQNRAQNQAgRQAgRTAgZTAwBVAAFUAQNVAQFWAANXAgVUAgRQBAdRBAdSBQhRBAlRBAhS' 
        'BAhRBgxTBgNZAQFbAQZaAwFcAABdAAFcAQNcAgVdAwZZBAVbBARcBApYBQpZBQhaBQ1dBw5fBwhU' 
        'CAhVCAtWCQtXCwxVCA9bCApdCg5fCw1eDRBbCRFfCRJeCRdfFRteEgFgAQBiAABjAABkAA1gBwxm' 
        'BgJqAQ1rBwhlCA9hDA9hDQ5iDhNkChVlCxBiDhFjDxNoCxRqCwBwAABzAAR3Agp1BQF6AQt5Bhlw' 
        'DR1yDxl7DRJmERZgFhdgFxZoFhtkGx1kHB1pHBJ7EiJ0EiN5EyJqIiFvISduJiZvJiZwJidxJyhy' 
        'KCt1Ky1zLTN2MzR2NDB5MDN5MzR8NDV+NTh+NgCBAACDAASAAgGMAAKNAQWNAgqOBhmADRyODwGW' 
        'AQiRBAmRBA2UBw+VCBOVCheaDBiaDRycDx2dDzCSCieSFSCfESGfES6fGCajFCekFSqiFymlFiql' 
        'Fi2nGDGpGTGpGjGqGjKqGjOuGjOuGyWxFSyxFy61GC+1GDCzGTGxGiSYJD+WPyChID6tITSvNDyi' 
        'PDW9NRPRChfTDR3RDxfaDBPIEyPHEifAFCfAFSbCFAvmBi3HLUGKQUaLRkWORUmPSUqOSkeRR0Gd' 
        'QU+WT1WaU1SaVFeZV0GmQUGtQU+iT0+mT0+rT1uhW1unW1+nX1upW1urW1usW2GjYWWoZWaqZmit' 
        'aGivaGmuaW6qbmiwaHC1cHS0dHS5dHW4dXW5dXa6dne6d3/Ef4C/gIHFgYTJhAAAAAAAAAAAAAAA' 
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAANwALAAAAAAWABYA' 
        'AAj+ALkJHEiwoMGDAoWgiRPnDZgUCAs2ocNLmrZt2Z7Z4mFBYApcBVeMWaatpMmS2exYMIGrC0ET' 
        'c6JVqzZt2kyaNasl21UtCkEgy5gJpXXGBgcgc4pBW7oUykAbtoYN4xWmgAEACgxcUCIKmTFjxJoM' 
        'FKOrrJcCCggiQILFlLBgwMRyy5Fm1qw0BUIU5GAF0KhfvnItEYjDTZ06NBRwUJuHlaxTpUKRgSEw' 
        'BJvLF9ISDLJiRYsWGyZsMCJQQY0bOlLojWhwQgELRaocucC6YI0QQqrg6UO54ISII6jc0SPoz4zf' 
        'lf1EDHGFOKFDk7hMcaLF0SNGhxD24DPoEKNJlzJKeQKV6dIkRoikGLywpVAiSJc6uWrVylUn82YK' 
        'HCzwZBElULCossoqqrhCShm0RTRDEopsgkosqXCSRW+1cXPBDySk8EOCFXY4UEAAOw==' )
        self.ICON_refresh = PhotoImage(data=refresh)

        icon_stop = (
        'R0lGODlhIAAgAOcAAAAAAKQAAKQBAaUBAaUCAqUDA6YDA6YEBLgEBLkEBLkFBcwAALoFBboGBs0B' 
        'Ac0CAs4CAs8DA7sJCc8EBL0JCdAFBdEFBb0LC9EGBr8MDNIHB78NDdMICNMJCdQJCdUKCtULC9YM' 
        'DMQREdcMDNcNDcUTE9gODqwaGq0aGtkPD60bG64bGtkQEK0cG60cHMcVFdoQEK4cHK0dHccWFsgW' 
        'Fq8dHdsSEtwSErAeHrEeHq4fHq8fH9wTE7AfH7EfH90UFLEgILEhId4VFd4WFrIiIt8WFrIjI98X' 
        'F+AXF+EYGOEZGeEaGuIaGuMaGuMbG+QcHOQdHeUdHeUeHuYeHuYfH+cfH+cgIOghIekiIuojI+ok' 
        'JOskJOwlJewmJu0nJ+4oKFVXU1dZVVhaVllcV1tdWVxeWl1fW15gW15gXF9gXV9hXWNlYWZoZWhq' 
        'Zm1va29wbHV3c3d5dH6Ae4OGgYaIg4eKhIuNiIuOiJGTjZOVkJaZk5mblpuemKCjnaKknqWooqmr' 
        'pqqtp62wqq6xqrCzrLG0rbS3sLW4sbe6s7q9tru+t7u+uL7Bur7Bu7/Bu7/BvL7CvL/CvNXHxdfK' 
        'x9jKx9jLyNrNytHR0N3OzNDSz9HSz9HS0N3PzdLS0N7PztLU0d/S0NXV1NbX1tna2Nrb2dvb2t3d' 
        '2+ja2t7e3N/g3urd3evd3Ove3eHh4Oze3uzf3+7f3+Lj4e7g4O/g4OPk4uXl4+Xm5PHj4+bn5Ofn' 
        '5efo5ujo5ujo5+nq6Ovr6evs6u3t6+3t7O7u7u/v7u/v7/Dw7/Dw8PHx8PHx8fLy8vLz8vPz8/T0' 
        '9PT19PX19Pb29fb39vf39vf39/f49/j4+Pj5+Pn5+Pn5+fr6+vv7+vv7+/z8/P39/f7+/v///wAA' 
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH+EUNyZWF0ZWQgd2l0aCBH' 
        'SU1QACH5BAEKAP8ALAAAAAAgACAAAAj+AP8JHEiwoMGDCBMqXMiwocOHEAcuSkSRIiJDhQYJijiw' 
        'kTVvIEOGfAaII6Nq3K6pXLmSmzM/EB1R2zaLyAEDBggMEBDAyK1tzPY4jDRtG6wcM7BYkQJlCRIh' 
        'G4LI2rYsD8NH0rS58kGjS5csV6Y4SSLkRoYdr7Qls6MQUrRsrHq84PLFy5awY4XwYHEBx6psyOYg' 
        'VAQNmyogJa5o4cIFrJS8N1KMoFDj1DVhcA4e8jYsiIgoVa5gwXKFyhMmSH7YSBHCg4Qgw7i5OUjI' 
        'G7AASpxEmVKFypQnTZIU4QHDBAgOFQ4A29bmYCBvvgIcCfkkZJKQKUJOKOAr25qDf7r+7QrwwxuA' 
        '80rMAzDPfj0AA7uunTnYZ1utADZCDhFinkf7kAAQUEs0YhzEhzaxBJACDO7dYB4M/50HwACxOAPG' 
        'QXpck0oAIQCYHQAkAGjeAgsIkIoyFxqERzSmBODBBxKGEAIAH3ggIQQAkBiAKcWkWNAdzZByQgMa' 
        'cNCBBx1wwIEGGFQQAQQkLoCADKQE4yNBddDSiyQoKFCBBRhgYEEFEzzpQJQIuDCJLZ+EgRAdrfRC' 
        'iQoMQGAnBA+cGaWULVSCSydqKCQHKr1Y4kICeyaKgAqW5LJJGgzFUYovnByaKIkIrIAJL5eg4dAb' 
        'o/wCig4BlGpqADF40ksmnj7Ehigswegi66yz/qJJqxCZEcoxxhTjazHEDDPMJWVwJNAYZCSrrLIF' 
        'Guvss9BGGxAAOw==' )
        self.ICON_stop =  PhotoImage(data=icon_stop)

        self.ICON_copy = (
            'R0lGODlhEAAQAPZKAGlrZ2psZ2psaGttaGttaWxvam1wa29xbG9xbW9ybXBybXN1cHR3cnh7dnl7' 
            'dnl9d3t9eH2Ae4CCfYKEf4SHgYeJhImLhouOiI2OjI2QipGTjZKUj5WYk5aZk5ialJmblZmblpqc' 
            'lpudl5uemJyfmZ2gmp6im6Oln6ampKanpaaopqusqqytq62tra2ura+vr7GxsObo5Ofp5ejq5unr' 
            '5unr5+rs6O3u6+7w7fDx7vHy8PHz8PLz8fT18/T19PX29fb39fb39vf39vj59/n5+Pn6+fv7+vv7' 
            '+/z8/P39/f///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5' 
            'BAEAAEsALAAAAAAQABAAAAeqgCcmJiMjIh4eHR0fS42NIkqRkpIbjo0dSjEyNTU2NjJKF5ZLG0o2' 
            'KCgqqTdKFaMYSjg5Ozw7tkoToxZKOSssLcBAShEfH4ofFEo9QERGSkRESg2TGxLKLS8wztEMnKAX' 
            'EEo7QEBDREPCCioqrBXTk5MItjtKEg8MCggFBQMDAAMYgg0blWwZtGfRGoyy1gPYi0jcRoUbV+5c' 
            'ulHv4EUyMOpePgP9/AVAEAgAOw==' )
        self.ICON_copy = PhotoImage(data=self.ICON_copy)


        self.ICON_merge = (
            'R0lGODlhGAAYAOeeAAAAAAEAAAMAAAQAAAEBAQIBAQMBAQcAAAACAgQBAQACAwECAwADAwADBAkB' 
            'AQIDAwIEBgAFBQ0CAgcEBAIGBwcFBQUGBgEHCAsFBQwFBQoGBhwCAhQFBgALDwUKDBAICCoBAR0F' 
            'BR0GBzABASgEBDgAACoEBCwEBDwAAAkODi4FBQsPEDEFBTMFBTUFBTkEBBwMDEcDAyAODhYREkcE' 
            'BDwHB1oAAFwAAEYGBjANDSUQEGMAAGQAAGYAAGsAAHEAAHQAAHkAAHwAAIEAAFENDn4BAXMEBIYA' 
            'AIcAAEYSEokAAIcBAY0AABAjKZUAAIgEBJUBAZsAAJwAAJ0AAJ4AAJ8AAKAAAKMAAKYAAKwAAFcX' 
            'F60AAK4AALAAALIAALMAALQAALYAALcAALoAALsAALwAABUtNMAAAMEAAMMAAGQaGsUAAMcAAGca' 
            'GskAAMoAAMsAAMwAAM4AAM8AANAAANEAANMAANQAANUAANYAANgAANkAANYBAdoAANsAAHAdHdwA' 
            'AN0AAN4AAN8AAOEAAOMAAOUAAOYAAOUBAekAAOoAAOgBAe4AAO8AAPAAAOoCAvIAAPQAAPUAAPcA' 
            'APwAAIIhIf0AADE4PD84OjU7QDY7QEU+QEI/QlNFRf//////////////////////////////////' 
            '////////////////////////////////////////////////////////////////////////////' 
            '////////////////////////////////////////////////////////////////////////////' 
            '////////////////////////////////////////////////////////////////////////////' 
            '////////////////////////////////////////////////////////////////////////////' 
            '/////////////////////////////////////////////////////yH+EUNyZWF0ZWQgd2l0aCBH' 
            'SU1QACH5BAEKAP8ALAAAAAAYABgAAAj+AP8JHEiwoMGDCBMqXIjwkoMdQIT4+LFhBcOBnP74OeQo' 
            'ESNIIQpc/KdJCxcpVbaIEdQnwMhMSa4gOaKEyRpGQwCM1KBDBgwORbAQQjTCgsAVDS4qELDEi6Q3' 
            'HwRiAIDgIgQUTsJIUtKjh5VHAzxcBGAjyqBGkSRNOgRHQgqGFDJM6eKGjh08eQKxifGA4YwnaOLY' 
            'xaNnTyBFOBYGEIFGzpw6d/LsAaSHiE6FBLLQiXMn0KBCfsbkuJxwAQ9DZ8AYaVGDBhUAFxYSALFI' 
            'ThglE3RWABDhoJkELlioeMFHDxkoB6ou7FSJEiVLlgp9uVIiKcNNbe7YsVNnTZYbpBcdYlJT5kya' 
            'NWeCAGAwsokBEyZIkDgRoMPI+/jxBwQAOw==' )
        self.ICON_merge = PhotoImage(data=self.ICON_merge)

        self.ICON_save = (     'R0lGODlhEAAQAPcAAAAAAAEBAQICAgYGBgkJCQ0NDBAREBQUExcYFxsbGh4fHR8fHiEiISIiISQl' 
            'IyUmJCcoJigpKCssKiwtLC4vLS8xLzEzMDIzMTM1MjU2NDk6Nzw9O0BBPkNFQUFFRENHRkZIRUVI' 
            'R0dKSElLSEpMSElMSktNSkpNS01PS0xPTU1QTU5RTk9ST1BST1FTUFJUUVNVUVNVUlRWUlRXU1VX' 
            'U1VXVFhZVlhaVllbV1tdWV5gXWBiXmFjX2FjYWNlYmRmYmRmY2RnZGVoZWZoZGdqaGhraWpubG1v' 
            'b21wb3BybXJ0b29xcHF0c3N1c3R1cnR2c3N2dXV3dHd4dXd5dXh5dnd6enp7eHt+eXx/eX1/e7MA' 
            'ANd5eX2Ae3+BfX+AfoCCf4OEgoaIhYmLhoiKh4qNh4iKiIqMioyOjI2Qio6Qjo6Qj5CTjZOWkJeZ' 
            'k5qclpuemLq+t7zAuL/Cu8DEvcTHwcXIwcjNxMvOx8zPyc3PytHUzdPWz9XX0tTX09XY09bY1NbZ' 
            '1Njb1dnc1drc19vd2N/h3OHj3uLi4uPl4ejp5u3u7O/v7/Dw7/X18/X19Pn5+P39/f///wAAAAAA' 
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAJIALAAAAAAQABAA' 
            'AAjxAFGQIKGloMGDGCxUIFFGzZaHECNWOTIBhBoVkRppbOSoo6NIH6BE6HAG46GTKE+CZPKAgxkX' 
            'kR7JnCkzUoglDDaUgREpZcpIIJYo0BCGRqSjjyJBWgopUgkjCTKAocHoqFWri04QQXDhCw0ZNL7K' 
            'gMGihYqzRA5Q4EKDyxs3bdaoQUOmy5MeQgxIsCKDzR5DiRYlQgToCg0mQQpAoCKDjCA7MmrcmQMo' 
            'iYwpPQg4eCKDiyA9MmTUgcPnB40pPAYw0PFDiSBBkePE4YODBpUdAiQtwBGEkCFAeerk6VNjR5Ya' 
            'uSUhyIGjRugazmUImD4gIAA7' )
        self.ICON_save = PhotoImage(data=self.ICON_save)

        self.ICON_filt = (
            'R0lGODlhGAAYAOfFAAABAAQHAgkPEQoQEgwREw0SFA4TFQ8UFhAVFxEVFxIWGBMXGRgXGhUZGhgc' 
            'HhscGh0hIyUjJiMkIiElJyImKCUpKyUpKyYqLCgsLiktLyouMCsvMSwwMi8zNS80NjA0NjE1NzI2' 
            'ODM3OTg2OTQ4OjU5OzU6PDY6PTc7PTw6PTg8Pjo+QDxBQ0JARD1CRDtDST9DRTxESj1ES0BERj9G' 
            'TUBHTkFIT0NISkJJUERJS0VKTElJUkNLUkZLTURMU0VNU0ZNVEdOVUlQV0pRWEtSWUxTWk1UW09U' 
            'Vk1VXFRVU05WXU9XXlJXWVBYX1FZYFNbYlVcZFhcXlldX1deZVhfZllgZ1phaFtjalxka11lbF5m' 
            'bV9nbmBob2FpcGJqcWNrcmRsc2VtdGZudWdvdmhwd2lxeGpyeWtzem10fG51fW92fnB3f3F4gHJ5' 
            'gXN6gnR7g3V8hHh9f3Z9hXl+gHd+hnh/h3p/gnmAiHqBiXuCin2ChXyDi32EjH6FjYCFiH+GjoCH' 
            'j4GIkIOIi4KJkYOKkn+LmISMk4eMj4WNlIaOlYePloSQnYWRnomRmIaSn4uTmoiUoYyUm5CUl4qV' 
            'oo2VnIuWo46WnoyXpI+Xn42YpZGZoY+ap5KaopGcqZKdqpWdpZmeoJSfrZefp5WgrpigqJahr5ei' 
            'sJqiqpijsZykrJmlsp6mrpuntJ6qt6Krs6CsuaGtuqKuvKautqOvvaSwvqiwuKy0vK21va+3v7G5' 
            'wrK7w7S9xba/x7zEzL3Fzb/H0MDJ0cHK0sLL08PM1MTN1f//////////////////////////////' 
            '////////////////////////////////////////////////////////////////////////////' 
            '////////////////////////////////////////////////////////////////////////////' 
            '/////////////////////////////////////////////////////yH+EUNyZWF0ZWQgd2l0aCBH' 
            'SU1QACH5BAEKAP8ALAAAAAAYABgAAAj+AP8JHEiwoMGDBYEoXIjQIJAgQowAATaM2DBfQKQICQIE' 
            'IQ0et3Dt4gWLFi1Yr1qxwmWLCQyDLmLIqpXJk6dSqlShGuWp06VHhXrkIPhBkiY6ePb8CTSIkNNA' 
            'gP7keVOmCJAUAyfEgXJGzRo3b+DIkUMHzhs3acpg0QEDwkAHH15M0eJFzJgxZfKWISMGC5QhKho0' 
            'KCiBQQcRiEGAIBFCRYkRGSoYCIAQBocECSpMoFDhggYNmA0YSIIwAKg5GzQIGECAgIECBVbVwtXw' 
            'X4A5RooY2V0Eypc1jCjXts07txErYt5MEj48Du8iRbKcqcN8uG3n0MW4qW49AHYnZugxcO+uG0qa' 
            '8db/xVlyBX36OE+2uLceZwqY+cP1bEGDv7YfMGw8kN5BgpDRX20PCFhbQAA7')
        self.ICON_filt = PhotoImage(data=self.ICON_filt)




    def setDefaultFonts(self):
       
        if self.platform == "Windows":
            courier = "Courier New"
            courier_size = "6"
            cygwin = BooleanVar()
            cygwin.set(False)
            import ctypes # used by CheckDiskSpace on Windows
        else:
            courier = "Courier"
            courier_size = "10"

        """
        helvisB=tkFont.Font(family="Helvetica",size=9,weight="bold")
        helvis=tkFont.Font(family="Helvetica",size=9)
        #helvis=tkFont.Font(family="Helvetica",size=9)
        helvis_underline=tkFont.Font(family="Helvetica",size=9, underline=1)
        small_font=tkFont.Font(family="Helvetica",size=8)
        helvisB10=tkFont.Font(family="Helvetica",size=10,weight='bold')
        courier=tkFont.Font(family='Courier', size = courier_size)

        self.FONTbold=helvisB
        self.FONT=helvis
        self.FONTmini = tkFont.Font(family="Helvetica",size=8)
        self.FONTnano = tkFont.Font(family="Helvetica",size=1)
        self.FONTmed = tkFont.Font(family="Helvetica",size=10, weight='bold')
        self.FONTboldTitle=helvisB10
        self.FONTsmall = small_font
        self.FONTunderline = helvis_underline
        """

        family = 'Bitstream vera sans'
        family = 'Arial'

        helvisB=tkFont.Font(family=family,size=9,weight="bold")
        helvis=tkFont.Font(family=family,size=9)
        #helvis=tkFont.Font(family="Helvetica",size=9)
        helvis_underline=tkFont.Font(family=family,size=9, underline=1)
        small_font=tkFont.Font(family=family,size=8)
        helvisB10=tkFont.Font(family=family,size=10,weight='bold')
        courier=tkFont.Font(family='Courier', size = courier_size)

        self.FONTbold=helvisB
        self.FONT=helvis
        self.FONTmini = tkFont.Font(family=family,size=8)
        self.FONTnano = tkFont.Font(family=family,size=1)
        self.FONTmed = tkFont.Font(family=family,size=10, weight='bold')
        self.FONTboldTitle=helvisB10
        self.FONTsmall = small_font
        self.FONTunderline = helvis_underline







        self.FONTcourier = courier
        courier_style = "roman"

        # Custom font setting:
        ## 2.7 disabled ## self.root.option_add( "*font", "Helvetica 9 bold")
        ## 2.7 disabled ## self.root.option_add( "*font", "Helvetica 9")
        #root.option_add( "*font", "Helvetica 8 bold")
        self.root.option_add( "*font", "Bitstream 9 bold")
        self.root.option_add( "*font", "Bitstream 9")
 

    def makeRaccoonGUI(self, root):
        self.OPAL_ligLib = []
        self.ligLibraryChoice = StringVar()

        self.root = root

        self.makeIcons()

        self.def_label_value = '[ click to set ]'
        # Font settings
        ## Courier-related settings
        self.setDefaultFonts()

        self.root.title('Raccoon OPAL | AutoDock VS')


        # create menu bar
        self.makeMenu(target=self.root)

        Pmw.initialise()
 
        #def foo(event=None):
        #    print self.notebook.getcurselection()
        #    print "RAISED"
        self.notebook = Pmw.NoteBook(self.root)
        self.tab0 = self.notebook.add('Opal Setup') # -> will become "Server selection" (including spawning local?)
        self.tab1 = self.notebook.add('Ligands')
        self.tab2 = self.notebook.add('Receptors')
        self.tab3 = self.notebook.add('Config') 
        self.tab5 = self.notebook.add('Jobs Manager')
        self.tab6 = self.notebook.add('Analysis')
        self.notebook.pack(padx=3, pady=5, fill=BOTH, expand=1)

        customrc = os.path.join(self.RACPATH, '_rac_pmvrc')
        self.embeddedViewer = EmbeddedMolViewer(customrc=customrc)
        self.molViewer = self.embeddedViewer.mv
        self.setDefaultFonts()
        

        #print self.notebook.pagenames()




        # button defaults
        self.default_button_opts_hor = {'anchor' : W, 'padx' : 3, 'pady' : 3,
                                    'expand': True, 'fill' : X, 'side' : LEFT}

        self.default_button_opts_ver = {'anchor' : N, 'padx' : 3, 'pady' : 3,
                                    'expand': False, 'side' : TOP}
        self.default_entry_opts = {'justify': RIGHT, 'bg': 'white'}


        # populate the opal setup tab
        self.GUImakeOpalSetupTab(self.tab0)
        # populate lig tab
        self.makeLigandTab(self.tab1)
        # populate rec tab
        self.makeRecTab(self.tab2)
        # populate grid tab
        self.GUImakeGridTab(self.tab3)

        # populate docking tab

        # populate generate tab
        self.GUImakeSubmitTab(self.tab5)

        #Button(self.root, text='TEST STATUS', command=self.updateStatus).pack()
        #Button(self.root, text='TEST CONNECTION', command=self.TESTCONN).pack()

        self.GUImakeAnalysisTab(self.tab6)



        #self.root.bind('<Control-Next>', self._nexttab)
        #self.root.bind('<Control-Prior>', self._prevtab)

        self.root.bind('<Control-Next>', lambda x: self.notebook.nextpage() )
        self.root.bind('<Control-Prior>', lambda x: self.notebook.previouspage() ) # self._prevtab)
        #self.root.bind('<Escape>', self.embeddedViewer._showPmv ) 
        self.root.bind('<F11>', self.embeddedViewer._showPmv ) 
        self.root.bind('<F12>', self.embeddedViewer._hidePmv ) 

        #self.notebook.bind('a', self._nexttab)

        #self.root.bind('', self._prevtab)

    def _nexttab(self, event=None):
        # XXX USELESS
        cur = self.notebook.index(Pmw.SELECT)
        #print cur, cur+1, len(self.notebook.pagenames())
        if cur + 1 > len(self.notebook.pagenames())-1:
            #print "end!"
            cur = -1
        self.notebook.selectpage(cur+1)
        #if self.notebook.page(Pmw.SELECT) == 'Config':
            
        #if cur+1 self.notebook.component(name+'-tab').bind('<1>', lambda x: 
        
        #self.embeddedViewer.activateCam(['rescam'], only=1))
        

    def _prevtab(self, event=None):
        # XXX USELESS
        cur = self.notebook.index(Pmw.SELECT)
        #print cur, cur-1, len(self.notebook.pagenames())
        if cur - 1 < 0: # len(self.notebook.pagenames())-1:
            #print "end!"
            cur = len(self.notebook.pagenames())
        self.notebook.selectpage(cur-1)
        
    def makeMenu(self, target):
        menubar = Pmw.MenuBar(target,
            hull_relief='raised',
            hull_borderwidth=1, balloon=None)
        menubar.pack(fill='x',anchor='n')
        self.menuBar=menubar
        menubar.addmenu('File',' ')
        menubar.addmenuitem('File','command', #balloonHelp=None, statusHelp=None,
            label="Preferences...",
            command=self._preferences)
        menubar.addmenuitem('File','separator')
        menubar.addmenuitem('File','command', #balloonHelp=None, statusHelp=None,
            label="Quit",
            command=self._quit)

        menubar.addmenu('Help', '', '', side='right')
        menubar.addmenuitem('Help','command',
            label='About RaccoonOpal',
            command=self._about)

    def _about(self):
        print "Show splashscreen"

    def _quit(self):
        title = 'Exit RaccoonOpal'
        msg = 'Do you want to quit Raccoon?'
        if askyesno(title, msg, parent=self.root):
            # check if interactive
            self.root.destroy()

    def _preferences(self):
        # - store ssh keys
        #   self.jobManTree.setDataFile(new_datafile)

        #OPAL_HISTORY="raccoon_opal.hist"
        #PAL_SERVERS="raccoon_opal_servers.conf"
        #OPAL_CONFIG='raccoon_opal.conf'
        def _setdatapath(event=None):
            title = 'Select the directory where to store result files'
            resdir = hf.userInputDir(parent=w, title = title, 
                initialdir=self.RESULTS_LOCATION, createnew=1) 
            if resdir:
                self.RESULTS_LOCATION = resdir
                labpath.configure(text=hf.truncateName(resdir, 55))
                self.writeRaccoonOpalConfig( values= { 'results_location': resdir } )

        def _setemail(event=None):
            self.setUserEmail(askfordefault=0, parent=g, allowempty=1)
            if self.OPAL_useremail.get().strip():
                email = self.OPAL_useremail.get() 
            else:
                email = '( not defined )'
            labemail.configure( text=email)
            


        def _setmaxresults(event=None, value=None):

            if value == None:
                title = 'Max number of results'
                prompt = "Set the top results cutoff:\n\n(set to '0' to disable the cutoff)"
                value = tks.askinteger(title, prompt, initialvalue=self.MAX_RESULTS,
                    minvalue=0, parent=g) 
            if not value == None:
                self.MAX_RESULTS=value
                self.writeRaccoonOpalConfig( values= { 'max_results': value } )
                if value == 0:
                    txt = "( unlimited )"
                else:
                    txt = "show only top %d results" % value
                labres.configure(text=txt)
                 

        win = Pmw.Dialog(self.root, title='Preferences', buttons=('Close',)) #, command=_close)
        w = win.interior()
        bwidth = 170
        lwidth = 40
        # data group
        g = Pmw.Group(w, tag_text = 'Local data', tag_font=self.FONTbold)
        g.grid(row = 1, column=1, sticky='we', padx=5, pady=5,ipadx=3,ipady=2)
        g = g.interior()
      
        Button(g, text='Set default data location...', anchor='w', image = self.ICON_small_folder, compound=LEFT,
            justify='left',
            command=_setdatapath,width=bwidth).grid(row=1, column=1, sticky='w', padx=3, pady=3)
        #Label(g, text=" ", bg='white', width=lwidth, font=self.FONT).grid(row=1, column=2, sticky='we', padx=3, pady=3)

        labpath = Label(g, text=hf.truncateName(self.RESULTS_LOCATION, 40), 
            highlightbackground='black', bg='white',
            highlightcolor='black', highlightthickness=1, 
            width=lwidth, font=self.FONT)
        labpath.grid(row=1, column=2, sticky='we', padx=3, pady=3)

        # remote and credentials
        g = Pmw.Group(w, tag_text = 'Remote access & credentials', tag_font=self.FONTbold)
        g.grid(row = 2, column=1, sticky='we', padx=5, pady=5,ipadx=3,ipady=2)
        g = g.interior()
      
        self.ICON_email = ImageTk.PhotoImage(file=os.path.join(self.ICONPATH, 'message.png'))

        #Button(g, text='Set default email...', image = self.ICON_small_folder, compound=LEFT,
        Button(g, text='Set default email...', anchor='w', image = self.ICON_email, compound=LEFT,
            command=_setemail,width=bwidth).grid(row=1, column=1, sticky='we', padx=3, pady=3)
        labemail = Label(g, text=hf.truncateName(self.OPAL_useremail.get(), 40),
            highlightbackground='black', bg='white',
            highlightcolor='black', highlightthickness=1, 
            width=lwidth, font=self.FONT)
        labemail.grid(row=1, column=2, sticky='we', padx=3, pady=3)

        # analysis settings
        g = Pmw.Group(w, tag_text = 'Analysis settings', tag_font=self.FONTbold)
        g.grid(row = 3, column=1, sticky='we', padx=5, pady=5, ipadx=3,ipady=2)
        g = g.interior()
      
        Button(g, text='Set default max. results...', anchor='w', image = self.ICON_small_folder, compound=LEFT,
            command=_setmaxresults,width=bwidth).grid(row=1, column=1, sticky='we', padx=3, pady=3)
        #if self.MAX_RESULTS == 0:
        #    txt = "( unlimited )"
        #else:
        #    txt = "%d top results" % self.MAX_RESULTS

        labres = Label(g, text='',
            highlightbackground='black', bg='white',
            highlightcolor='black', highlightthickness=1, 
            width=lwidth, font=self.FONT)
        labres.grid(row=1, column=2, sticky='we', padx=3, pady=3)
        _setmaxresults(value=self.MAX_RESULTS)



    
        

        win.winfo_toplevel().resizable(NO,NO)
        win.activate(geometry='centerscreenalways')



##############################
### LIGAND  
##############################


    def makeLigandTab(self, target = None):
        # buttons
        #     add, add_d, rm, rm_all, filter, PDBQTopts
        # lig_container
        #       status (acceted:x, rejected:x)
        #     -------------------------
        if not target:
            print "makeLigandTab> nothing to do, no target"
            return

        ### button panel
        target.buttons = Frame(target)
        target.buttons.pack(side=TOP, expand=False, fill=X, anchor=N, padx=3, pady=3)

        # refresh ligands list
        #refresh_lig_list = Button(target.buttons, text = 'Refresh library', command = self.GUI_OPALrefreshLigLib)
        #refresh_lig_list.pack(self.default_button_opts_hor)


        self.ligLibraryChoice = StringVar()

        #print self.OPAL_ligLib, type(self.OPAL_ligLib)

        self.ligLibraryPulldown = OptionMenuFix(target,
                   labelpos='w',
                   label_text="Ligand library :",
                   label_font=self.FONTbold,
                   menubutton_width=60,
                   menubutton_textvariable=self.ligLibraryChoice,
                   menubutton_font=self.FONT,
                   items=self.OPAL_ligLib,
                   command=self.updateStatus)
        self.ligLibraryPulldown.pack(anchor=CENTER,side=TOP)

        frame_info = Pmw.Group(target, tag_text = "Library info")

        Label(frame_info.interior(), text="Ligands  :", justify=LEFT, width=25,font=self.FONTbold).grid(row=1, column=1,sticky=E)
        Label(frame_info.interior(), text="...many...", justify=LEFT).grid(row=1, column=2,sticky=W)

        Label(frame_info.interior(), text="Source  :", justify=LEFT, width=25,font=self.FONTbold).grid(row=3, column=1,sticky=W)
        Label(frame_info.interior(), text="somewhere in California", justify=LEFT).grid(row=3, column=2,sticky=W)

        Label(frame_info.interior(), text="Properties range :", justify=LEFT, width=25,font=self.FONTbold).grid(row=5, column=1,sticky=W)
        Label(frame_info.interior(), text="HBA[0,oO]...", justify=LEFT).grid(row=5, column=2,sticky=W)

        Label(frame_info.interior(), text="Atom types present:", justify=LEFT, width=25,font=self.FONTbold).grid(row=7, column=1,sticky=W)
        Label(frame_info.interior(), text="A,C,X,W,3,$,%", justify=LEFT).grid(row=7, column=2,sticky=W)

        Label(frame_info.interior(), text="Comments :", justify=LEFT, width=25,font=self.FONTbold).grid(row=9, column=1,sticky=W)
        Label(frame_info.interior(), text="A nice library with a lot of compounds\nobtained in obscure ways....", justify=LEFT).grid(row=9, column=2,sticky=W)

        frame_info.pack(side=TOP, anchor=NW, expand=N,fill=X)



    def GUI_OPALrefreshLigLib(self, *args):
        if self.debug: print "refreshing ligands list"
        if self.debug: print "URL SELECTED:", self.OPALurl.get()
        try:
        #if 1:
            if self.debug: print "LIBS", self.Opal_getListofLibraries()

            self.OPAL_ligLib = self.Opal_getListofLibraries()
            self.ligLibraryPulldown.setitems(self.OPAL_ligLib)
            self.ligLibraryChoice.set("")
        #else:
        except:
            error = sys.exc_info()[1]
            print "ERROR!:", error
            showwarning("Server error", "Impossible to get ligand library info.\n\n(server down/unreachable?)\n\n%s" % error)
            self.initOpalStuff()
        self.updateStatus()

    def Opal_getListofLibraries(self):
        if self.OPALurl.get() == "":
            print "NO URL YET!"
            return
        metadata = self.OpalService.getServiceMetadata()
        for item in metadata._types._taggedParams._param:
            if item._id == 'ligand_db':
                return item._value

##############################
### RECEPTOR
##############################



    def makeRecTab(self, target=None):
        if target==None:
            target = self.tab2

        self.GUI_var_RecCount = StringVar(value='Accepted receptors : 0')
        Label(target, textvar = self.GUI_var_RecCount, justify=LEFT).pack(side=TOP, anchor=W, expand=N,fill=X)

        ### button panel
        target.buttons = Frame(target)


        # buttons
        # add lingand
        load_single_rec = Button(target.buttons, #text='+', 
            command = self.GUIloadRecFiles, 
            compound=LEFT,image=self.ICON_open_file)
        load_single_rec.pack(self.default_button_opts_ver)

        # add directory (window)
        scan_directory = Button(target.buttons, #text='[_|...',
            command = self.GUIscanDirForRecs,
            compound=LEFT, image=self.ICON_open_dir)
        scan_directory.pack(self.default_button_opts_ver)

        # remove selected
        remove_selected = Button(target.buttons, #text='X', 
            command = self.GUIremoveSelRecs,
            compound=LEFT, image=self.ICON_remove_sel)
        remove_selected.pack(self.default_button_opts_ver)

        # remove all
        remove_all = Button(target.buttons, #text='[^]',
            command = self.GUIremoveAllRecs,
            compound = LEFT, image=self.ICON_remove_all)
        remove_all.pack(self.default_button_opts_ver)
               
        # pdbqt options
        pdbqt_convert_opt = Button(target.buttons, #text='O', 
            command = self.GUIpdbqtConvertOptRec,
            compound=LEFT,image=self.ICON_settings)
        opts = self.default_button_opts_hor
        opts['side'] = BOTTOM
        pdbqt_convert_opt.pack(self.default_button_opts_hor)

        target.buttons.pack(side=LEFT, expand=0, fill=Y, anchor=NW, padx=3, pady=3)

        right_frame = Frame(target)
        # receptors count
        #self.GUI_var_RecCount = StringVar(value='Accepted receptors : 0')
        #Label(right_frame, textvar = self.GUI_var_RecCount, justify=LEFT).pack(side=TOP, anchor=N, expand=N,fill=X)
        
        #

        ### receptor container
        target.recContainer = TkTreectrl.ScrolledMultiListbox(right_frame, bd=2)
        target.recContainer.listbox.config(bg='white',fg='black',font=self.FONT,
            columns=('Name', 'chains', 'res.','flex_res','atom types','unk.types',
                'filename'), expandcolumns=(0,6), selectmode='extended')
        target.recContainer.pack(side=TOP,anchor=NW,expand=Y,fill=BOTH) 
        target.recContainer.listbox.bind('<Double-Button-1>',  lambda x: self.GUIloadRecFiles() )
        right_frame.pack(side=LEFT,anchor=NW,expand=Y,fill=BOTH)



    def GUIloadRecFiles(self):
        #print "GUIloadRecFiles>"
        """ single window file-selector for specifying receptor files
        """
        title = 'Select one or more supported receptor files'
        filetypes = [("Supported ligand formats", ("*.pdbqt", "*.mol2", "*.pdb" )), # XXX include case-sensitive alternate
                     ("PDBQT", "*.pdbqt"), ("PDB", "*.pdb"), ("Mol2", "*.mol2"), 
                     ("Any file type...", "*")]
        rec_list = askopenfilename(parent=self.root, title = title, filetypes = filetypes, multiple = 1)
        if not type(rec_list) == type([]):
            rec_list = self.root.splitlist(rec_list)
        pdb_list, pdbqt_list, mol2_list = [],[],[]
        master_rejected = {}
        for l in rec_list:
            name, ext = os.path.splitext(l)
            if (ext == '.pdb') or (ext=='.PDB'): 
                pdb_list.append(l)
            elif (ext == '.pdbqt') or (ext=='.PDBQT'):
                pdbqt_list.append(l)
            elif (ext == '.mol2') or (ext=='.MOL2'):
                mol2_list.append(l)
            else:
                print "Unrecognized extension>", name, ext
        if len(pdbqt_list):
            #accepted, rejected = self.checkPdbqtList(pdbqt_list, mode='lig')
            result = self.addReceptorList(pdbqt_list)
            if self.debug: 
                print "GUIloadRecFiles> problematic", len(result['rejected'])
                print "GUIloadRecFiles> pdbqt", len(result['accepted'])
            self.GUIupdateRecList(action='add', receptors=result['accepted'])

            if len(result['rejected']):
                master_rejected['PDBQT'] = result['rejected']
            #self.GUIupdateRecCount()
        if len(pdb_list):
            print "GUIloadLigandfiles> PDB got here..."
            print pdb_list
            result['rejected'] = []
            # XXX todo
            # XXX process pdb_list
            if len(results['reject']):
                master_rejected['PDB'] = result['rejected']

                
        if len(mol2_list):
            # XXX todo
            if self.debug: print "GUIloadLigandfiles> MOL2 got here..."
            result['rejected'] = []
            # XXX todo
            # XXX process pdb_list
            if len(results['reject']):
                master_rejected['MOL2'] = result['rejected']

        # test if masterRejecetd is populated
        if len(master_rejected.keys())>0:
            tot = 0
            for i in master_rejected.keys():
                tot += len(master_rejected[i])
            title = 'Problematic structures'
            msg = ('%d structure(s) have been rejected.\n'
                   'Do you want to inspect the log?') % tot
            if askyesno('Problematic structures', msg):
                self.GUIshowFilesImportReport(data_dict = master_rejected,
                    parent = self.root, title = 'Problematic receptor structures')

    def GUIshowFilesImportReport(self, parent = None, title = 'Problematic files', data_dict={}):
        """show a mini-notebook with tabs for problematic files imported divided by type"""
        win = Pmw.Dialog(parent = self.root, title = 'Problematic structures',
            buttons=('Close',))

        #Label(win.interior(), text = 'stuf and stuff'+str(master_rejected)).pack()
        w = win.interior()
           
        nb = Pmw.NoteBook(w)
        for t in data_dict.keys():
            tab = nb.add(t)
            mlb = TkTreectrl.ScrolledMultiListbox(tab, bd=2)
            mlb.listbox.config(bg='white',fg='black',font=self.FONT,
                    columns=('issue', 'filename'), expandcolumns=(0,1), selectmode='single')
            for f in data_dict[t]:
                mlb.listbox.insert('end', f[0], f[1])
            mlb.pack(expand=1,fill='both',padx=3, pady=3)
        # naturalsize
        nb.pack(padx=3,pady=3, fill='both', expand=1)

        # XXX todo add exporting functionalities?
        win.activate()





    def GUIscanDirForRecs(self):
        print "GUIscanDirForRecs>"
        return

    def GUIremoveSelRecs(self):
        if self.debug: print "GUIremoveSelRecs>"
        for i in self.tab2.recContainer.listbox.curselection():
            tdata = self.tab2.recContainer.listbox.get(i)[0]
            fname = tdata[6]
            rname = tdata[0]
            
            self.removeReceptors( [rname] )
            self.tab2.recContainer.listbox.delete(i)

        self.GUI_rec_list_container.delete(0,END)
        for r in self.RecBook.keys():
            rec_data = self.RecBook[r]
            self.GUI_rec_list_container.insert('end', rec_data['name'])
        self.GUIupdateRecCount()

        return
    
    def GUIremoveAllRecs(self):
        """ handle request from GUI to remove all receptors"""
        if self.debug: print "GUIremoveAllRecs>"
        rec_count = len(self.RecBook.keys())
        if rec_count == 0: return
        text = "All receptors (%d) are going to be deleted from the session\nAre you sure?"
        text = text % rec_count
        if askyesno('Removing all receptors', text, icon=WARNING) or rec_count == 1:
            self.removeReceptors()
            self.tab2.recContainer.listbox.delete(0,END)
            self.GUI_rec_list_container.delete(0,END)
            self.GUIupdateRecCount()

    def GUIupdateRecList(self, action='add', receptors=None):
        """ action = 'add' -> ligand info are added to the ligand container list
                     'del' -> ligand is deleted from the ligand container list
        """          
        for rec in receptors:
            if action=='add':
                r = rec[0]
                rec_data = self.RecBook[r]
                types = ""
                unk=''
                flex_res = '[no]'
                chains = ''
                for a in sort(rec_data['atypes']):
                    types+=" %s" % a
                types = types.strip()
                for a in sort(rec_data['atypes_unknown']):
                    unk += ' %s' % a
                unk = unk.strip()
                if rec_data['is_flexible']: # in rec_data.keys():
                    #print "ISFLEXI"
                    flex_res = " ".join(rec_data['flex_res'])
                chains = " ".join(rec_data['chains'])
                self.tab2.recContainer.listbox.insert('end',rec_data['name'], chains, 
                    len(rec_data['residues']), flex_res, types, unk, rec_data['filename'])

                self.GUI_rec_list_container.insert('end', rec_data['name'])
            elif action=='del':
                #print "FIND A WAY TO DELETE SOMETHING FROM self.tab2.recContainer"
                # find the index!
                #self.tab1.ligContainer.listbox.delete(0,END)
                # XXX Obsolete
                pass
        self.GUIupdateRecCount()


    def GUIpdbqtConvertOptRec(self):
        """open window to set PDBQT conversion options"""
        print "GUIpdbqtConverOpt>"
        return

    def GUIupdateRecCount(self):
        print "GUIupdateRecCount>"
        msg = "Accepted receptors : %d" % len(self.RecBook)
        self.GUI_var_RecCount.set(msg)
        pass







##############################
### CONFIG
##############################



    def GUImakeGridTab(self, target, viewer = True): # , mode='autodock'):
    
        from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
        from mglutil.util.callback import CallbackFunction


        def setWheelBox(wheelname, value):
            #print "WHEELNAME CALLED", wheelname,value
            if not viewer:
                return
            cx, cy, cz = self.box_center #box.center
            sx, sy, sz = self.box_size
            data = self.gridBox()
            if cx == None or sx == None:
                #print "SOMETHING MISSING IN THE cENTERSIZE"
                return
            if wheelname=='center_x':
                cx = value
                #self.GUI_box3D.Set(center = (cx, cy, cz))
            elif wheelname=='center_y':
                cy = value
                #self.GUI_box3D.Set(center = (cx, cy, cz))
            elif wheelname=='center_z':
                cz = value
                #self.GUI_box3D.Set(center = (cx, cy, cz))
            elif wheelname=='size_x':
                #self.GUI_box3D.Set(sx = value)
                sx = value
            elif wheelname=='size_y':
                #self.GUI_box3D.Set(sy = value)
                sy = value
            elif wheelname=='size_z':
                sz = value
                #self.GUI_box3D.Set(sz = value)

            self.GUI_box3D.Set(center = (cx, cy, cz))
            self.GUI_box3D.Set(xside=sx, yside=sy , zside=sz)
            self.box_center = [ cx, cy, cz ]
            self.box_size = [ sx, sy, sz ]

            self.syncConfGUISettings()

            self.updateStatus()



        # XXX use teh function to 'follow' a variable

        target.vinaParmPanel = Frame(target) # Supercontainer

        #def nothing(*arg):
        #    print "nothing", arg
            #print "VALUE", arg[0].get()
            # check if there are residues in the box

        #
        #  _(\-/)_
        # {(#b^d#)} 
        # `-.(Y).-` 
        #

        left_frame = Frame(target)
        Button(left_frame, text='Import config file...', command = self.GUI_importVinaConf, font=self.FONT,
        compound=LEFT,image=self.ICON_small_folder).pack(side = TOP, anchor=N, expand=N,fill=X,pady=5)      


        self.GUI_Grid_thumbwheel_array = []

        # center group
        c_group = Pmw.Group(left_frame, tag_text = 'Center',tag_font = self.FONTbold)

        colors = { 'center_x' : '#ff3333',
                   'center_y' : 'green',
                   'center_z' : '#00aaff',
                   'size_x' : '#ff3333',
                   'size_y' : 'green',
                   'size_z' : '#0099ff',

                   }

        for lab in ['center_x', 'center_y', 'center_z']:
            cb = CallbackFunction(setWheelBox, lab)
            tw = ThumbWheel(
                c_group.interior(), labCfg={'text':lab, 'side':'left','fg':colors[lab],
                'bg':'black', 'width':9 }, showLabel=1,
                width=90, height=14, type=float, value=0.0,
                callback=cb, continuous=True,
                oneTurn=5, wheelPad=0)
            tw.pack(side='top', pady=5,anchor=N)
            self.GUI_Grid_thumbwheel_array.append(tw)
        c_group.pack(side=TOP, anchor=N, expand=N,fill=X,ipadx=3,ipady=3)

        # size group
        s_group = Pmw.Group(left_frame, tag_text = 'Size', tag_font=self.FONTbold)

        for lab in ['size_x', 'size_y', 'size_z']:
            cb = CallbackFunction(setWheelBox, lab)
            tw = ThumbWheel(
                s_group.interior(), labCfg={'text':lab, 'side':'left', 
                'fg':colors[lab],'bg':'black','width':10}
                , showLabel=1,
                width=90, height=14, type=float, value=0.0,
                callback=cb, continuous=True,
                oneTurn=5, wheelPad=0)
            tw.pack(side='top', pady=5,anchor=N)
            self.GUI_Grid_thumbwheel_array.append(tw)
        s_group.pack(side=TOP, anchor=N, expand=N,fill=X,ipadx=3,ipady=3)
        

        searchF = Pmw.Group(left_frame, tag_text = 'Search parmeters', tag_font=self.FONTbold)
        
        f = Frame(searchF.interior())
        Label(f, text = 'exhaustiveness', justify=CENTER,font=self.FONT).grid(row=1, column=1,sticky=W)
        self.vina_GUI_exhaustiveness = Entry(f, width=8, justify=RIGHT,bg='white')
        self.vina_GUI_exhaustiveness.grid(row=1,column=2,sticky=E, padx=5,pady=3)
        Button(f, image=self.ICON_default, command = lambda : self.GUI_setDefault('exhaustiveness')).grid(row=1,column=3,sticky=E,padx=2,pady=2)
        #f.pack(side=TOP,anchor=N)

        #f = Frame(searchF.interior())
        Label(f, text = 'num.modes', justify=CENTER,font=self.FONT).grid(row=2, column=1,sticky=W)
        self.vina_GUI_numModes = Entry(f, width=8, justify=RIGHT,bg='white')
        self.vina_GUI_numModes.grid(row=2,column=2,sticky=E, padx=5,pady=3)
        Button(f, image=self.ICON_default, command = lambda : self.GUI_setDefault('num.modes')).grid(row=2,column=3,sticky=E,padx=2,pady=2)

        #f.pack(side=TOP,anchor=N)

        #f = Frame(searchF.interior())
        Label(f, text = 'energy range',justify=CENTER,font=self.FONT).grid(row=3, column=1,sticky=W)
        self.vina_GUI_energyRange = Entry(f, width=8, justify=RIGHT,bg='white')
        self.vina_GUI_energyRange.grid(row=3,column=2,sticky=E, padx=5,pady=3)
        Button(f, image=self.ICON_default, command = lambda : self.GUI_setDefault('energy range')).grid(row=3,column=3,sticky=E,padx=2,pady=2)
        f.pack(side=TOP,anchor=N)

        searchF.pack(side=TOP, anchor=N)


        f = Pmw.Group(left_frame, tag_text='Receptors', tag_font=self.FONTbold)
        self.GUI_rec_list_container = Listbox(f.interior(), bg='white')
        self.GUI_rec_list_container.pack(anchor=N, side=TOP,expand=Y,fill=BOTH)
        self.GUI_rec_list_container.bind('<ButtonRelease-1>', self.GUI_loadRecViewer)
        f.pack(anchor=N,side=TOP, expand=Y,fill=BOTH)

        left_frame.pack(side=LEFT,anchor=N, expand=N,fill=Y)

        # 3d box is created here viewer is created here...
        if viewer:
            right_frame = Pmw.Group(target, tag_text='3D viewer', tag_font=self.FONTbold)
            self.make3DboxViewer(right_frame.interior())
            #self.tab3 = self.notebook.add('Config') 
            name = 'Config'
            #self.notebook.component(name+'-tab').bind('<1>', lambda x: self.embeddedViewer.activateCam(['boxcam'], only=1))
            self.notebook.component(name+'-tab').bind('<1>', lambda x: self._switchCams('boxcam') )
            #self.tab3.bind_all('<1>', lambda x : self.embeddedViewer.activateCam(['boxcam'], only=1))
            right_frame.pack(side=LEFT,anchor=N, expand=Y,fill=BOTH, padx=5,pady=0)
        target.vinaParmPanel.pack(expand=Y,fill=BOTH, ipadx=3, ipady=3)
        #
        ################### AUTODOCK END
        
        ################### VINA END
        #
        target.vinaGrid = Frame(target)
        self.GUI_setDefault()

    """
    def _activatecam(self, namelist=[], only=1):
        # - hide/delete all res molecules
        # - reactivate this camera
        print "_activatecam> namelist", namelist
        #self.embeddedViewer.addCamera(target, name = 'boxcam')
        for c in self.embeddedViewer.cameras.keys():
            print "PROCESSING", c
            if self.embeddedViewer.cameras[c]['name'] in namelist:
                self.embeddedViewer.cameras[c]['obj'].suspendRedraw = 0
            elif only:
                self.embeddedViewer.cameras[c]['obj'].suspendRedraw = 1

    def _deactivatecam(self, namelist=[]):
        if len(namelist) == 0:
            namelist = self.camerasDic.keys()
        for c in namelist:
            self.camerasDic[c].suspendRedraw = 1
    """

    def GUI_setDefault(self, request=None):
        widgets = [  self.vina_GUI_exhaustiveness, 
                     self.vina_GUI_numModes,
                     self.vina_GUI_energyRange,
                  ]

        values = []
        wid = []
        if request in ['exhaustiveness', None]:
            values.append(8)
            wid.append(widgets[0])
            #self.vina_GUI_exhaustiveness.insert(8)
        if request in ['num.modes', None]:
            values.append(9)
            wid.append(widgets[1])
        if request in ['energy range', None]:
            values.append(3)
            wid.append(widgets[2])
        for i in range(len(values)):
            #print "adding something", request
            wid[i].delete(0,END)
            wid[i].insert(0, values[i])



    def make3DboxViewer(self, target):

        self.embeddedViewer.addCamera(target, name = 'boxcam')

        #self.embeddedViewer.VIEWER.GUI.depthcued.set( 1 )
        #self.embeddedViewer.VIEWER.Depth_cb_arg(None)
        #self.embeddedViewer.VIEWER.AutoDepthCue(None)
        
        # the viewer things fog is on, but it is not for this cam...
        cam = self.embeddedViewer.camByName('boxcam')
        cam.fog.Set(enabled=1)   
        from DejaVu.Box import Box
        from MolKit import Read
        self.GUI_box3D = Box('Vina_box')
        self.GUI_box3D.Set(xside=0.001, yside=0.001, zside=0.001)
        self.molViewer.GUI.VIEWER.AddObject(self.GUI_box3D)
        #self.GUI_box3D.hiddenInCamera[res_cam] = True

 
    def GUI_loadRecViewer(self, *arg):
        try:
            sel =  self.GUI_rec_list_container.curselection()
        except:
            #print "NO SELECTION"
            return
        if not sel:
            self.notebook.selectpage('Receptors') 
            
            return
        #print "SEL IS", sel
        #print "SEL", sel, sel[0]
        rec_name = self.GUI_rec_list_container.get(sel)
        self.loadReceptorInViewer(rec_name)
        
    def loadReceptorInViewer(self, rec):
        try:
            for m in self.CURRENT_RECEPTOR:
                self.molViewer.deleteMol(m)
        except:
            if self.debug: print "loadReceptorInViewer> no receptor yet"
        
        try:
            # rigid receptor
            self.CURRENT_RECEPTOR = [ self.molViewer.readMolecule( self.RecBook[rec]['filename'])[0] ]
            # color
            carbons = "%s:::C*" % self.CURRENT_RECEPTOR[-1].name
            self.molViewer.colorByAtomType(self.CURRENT_RECEPTOR[-1], ['lines', 'balls', 'sticks'], log=0)  

            # flex receptor
            if self.RecBook[rec]['is_flexible']:
                self.CURRENT_RECEPTOR.append( self.molViewer.readMolecule( self.RecBook[rec]['flex_res_file'])[0] )
                m = self.CURRENT_RECEPTOR[-1] 
                # style
                #self.molViewer.displaySticksAndBalls(m, cquality=0, sticksBallsLicorice='Licorice',
                #        bquality=0, cradius=0.2, setScale=True, only=False, bRad=0.3, negate=False, bScale=0.0, redraw=True)
                self.molViewer.displaySticksAndBalls(m, cquality=0, sticksBallsLicorice='Licorice',
                        bquality=0, cradius=0.2, setScale=True, only=False, bRad=0.3, negate=False, bScale=0.0, redraw=True)
                # color
                carbons = "%s:::C*" % m.name
                self.molViewer.colorByAtomType(m, ['lines', 'balls', 'sticks'], log=0)  
                self.molViewer.color(carbons, [[0.51764705882352946, 1.0, 0.0]], ['lines', 'balls', 'sticks'], log=0)  
        except:
            if self.debug: print "loadReceptorInViewer> catched potential PMV.readMolecule error..."


        # limit cam visibility
        res_cam = self.embeddedViewer.camByName('rescam')

        for mol in self.CURRENT_RECEPTOR:
            for g in mol.geomContainer.geoms.keys(): #rec_geom:
                geom = mol.geomContainer.geoms[g]
                geom.hiddenInCamera[res_cam] = True 



    def GUI_importVinaConf(self, fname=None):
        if not fname:
            title = "Select Vina config file to import"
            filetypes = [("Vina config file", ("*.conf", "*.CONF")),
                         ("Any file...", ("*")) ]
            
            fname = askopenfilename(parent=self.root, title = title, filetypes = filetypes, multiple = 0)
	    print "XXXTYPE", type(fname)
	    print "|%s|" % fname
        if not fname: return
        conf_data = self.gridBoxFromConf(fname)
        if not conf_data:
            print "error parsing conf data"
            showwarning('Config file', 'The config file contains some errors', parent=self.root)
            return

        ex = self.vina_settings['exhaustiveness']
        num_modes = self.vina_settings['num_modes']
        energy_range = self.vina_settings['energy_range']

        box_data = self.gridBox()
        try:
            self.GUI_Grid_thumbwheel_array[0].set( box_data['center'][0])
            self.GUI_Grid_thumbwheel_array[1].set( box_data['center'][1])
            self.GUI_Grid_thumbwheel_array[2].set( box_data['center'][2])
    
            self.GUI_Grid_thumbwheel_array[3].set( box_data['size'][0])
            self.GUI_Grid_thumbwheel_array[4].set( box_data['size'][1])
            self.GUI_Grid_thumbwheel_array[5].set( box_data['size'][2])
            #if 'exhaustiveness' in conf_data:
            if conf_data['exhaustiveness']: # in conf_data:
                self.vina_GUI_exhaustiveness.delete(0,END)
                self.vina_GUI_exhaustiveness.insert(0, conf_data['exhaustiveness'])
                self.vina_settings['exhaustiveness'] = conf_data['exhaustiveness']

            #if 'num_modes' in conf_data:
            if conf_data['num_modes']: # in conf_data:
                self.vina_GUI_numModes.delete(0,END)
                self.vina_GUI_numModes.insert(0, conf_data['num_modes'])
                self.vina_settings['num_modes'] = conf_data['num_modes']
            if conf_data['energy_range']: # in conf_data:
                self.vina_GUI_energyRange.delete(0,END)
                self.vina_GUI_energyRange.insert(0, conf_data['energy_range'])
                self.vina_settings['energy_range'] = conf_data['energy_range']
            

            #self.vina_GUI_exhaustiveness
            #     self.vina_GUI_numModes,
            #     self.vina_GUI_energyRange,

            # XXX TODO set exhaustiveness , nummodes etc...
        except:
            print "\n\nGUI_importVinaConf> ### !!! ### some error in importing the CONFIG data...", exc_info()[1]
            pass

        self.updateStatus()


##############################
### OPAL SETUP
##############################

    
    def GUImakeOpalSetupTab(self, target):

        #Label(searchParm_frame, text = 'write log file', width = 18, justify=CENTER).grid(row=4, column=1,sticky=E)
        #Entry(searchParm_frame, width=8, textvar= self.vina_energyRange, justify=RIGHT,bg='white').grid(row=3,column=2,sticky=E)

        self.OPALurl = StringVar()
        #self.OPAL_servers_list = []

        #print self.OPAL_servers_list, type(self.OPAL_servers_list)

        choice_frame = Frame(target)

        Button(choice_frame, text="Setup...", justify=RIGHT, #width = 20,
            compound=LEFT,image=self.ICON_settings,
            command=self.GUI_OPAL_addToServerList).pack(anchor=NW,side=RIGHT)

        self.OPALserverPulldown = OptionMenuFix(choice_frame,
                   labelpos='w',
                   label_text="Service choice :",
                   label_font = self.FONT,
                   menubutton_width=80,menubutton_height=1,
                   menubutton_font=self.FONTbold,
                   menubutton_textvariable=self.OPALurl,
                   items=self.OPAL_servers_list,
                   command=self.updateOpalServer)
        self.OPALserverPulldown.pack(anchor=NW,side=RIGHT,expand=Y,fill=BOTH)

        choice_frame.pack(anchor=NW,side=TOP)

        #frame_info = Frame(target)
        frame_info = Pmw.Group(target, tag_text = "Server info", tag_font=self.FONTbold)

        Label(frame_info.interior(), text="Location :", justify=LEFT, width=25,font=self.FONTbold).grid(row=1, column=1,sticky=W)
        Label(frame_info.interior(), text="Earth", justify=LEFT).grid(row=1, column=2,sticky=W)

        Label(frame_info.interior(), text="Credentials :", justify=LEFT, width=25,font=self.FONTbold).grid(row=3, column=1,sticky=W)
        Label(frame_info.interior(), text="RSA key... maybe?", justify=LEFT).grid(row=3, column=2,sticky=W)

        Label(frame_info.interior(), text="Features :", justify=LEFT, width=25,font=self.FONTbold).grid(row=5, column=1,sticky=W)
        Label(frame_info.interior(), text="several...", justify=LEFT).grid(row=5, column=2,sticky=W)

        Label(frame_info.interior(), text="Accept user ligands :", justify=LEFT, width=25,font=self.FONTbold).grid(row=7, column=1,sticky=W)
        Label(frame_info.interior(), text="probably not", justify=LEFT).grid(row=7, column=2,sticky=W)

        Label(frame_info.interior(), text="Accept user receptors :", justify=LEFT, width=25,font=self.FONTbold).grid(row=9, column=1,sticky=W)
        Label(frame_info.interior(), text="most likely but not sure...", justify=LEFT).grid(row=9, column=2,sticky=W)


        frame_info.pack(side=TOP, anchor=NW, expand=N,fill=X)
        #def GUI_OPALrefreshLigLib(self):
   

    def GUI_OPAL_update_server_pulldown(self):
        self.OPALserverPulldown.setitems(self.OPAL_servers_list)




    def addNewServerStatic(self, link, check=True, temporary=False):
        """ add permanently a server to the session """
        if check:
            try:
                if self.debug: print "SERVER CHECKCODE", urllib.urlopen(link).info()
            except:
                print "ERROR", exc_info()[0], exc_info()[1]
                if not askyesno("Server unreachable/error", 
                    ('The server at the address\n\n"%s"\n\nseems to be unreachable.\n\nAdd anyway?'% link)):
                    return False  
        if not link in self.OPAL_servers_list:
            self.OPAL_servers_list.append(link)
        else:
            return False
        if not temporary:
            self.addServerFromFile(link)
        return True

    def addServerFromFile(self,link):
        fp = open(self.OPAL_SERVERS,'a')
        fp.write(link+'\n')
        fp.close()

    def removeServerFromFile(self, link):
        curr_lines = getLines(self.OPAL_SERVERS, doStrip=1)
        try:
            idx = curr_lines.index(link)
            del curr_lines[idx]

            writeList(self.OPAL_SERVERS, curr_lines, addNewLine=1)
        except:
            print "ERROR! when trying to open %s and remove %s\n%s" % (self.OPAL_SERVERS, link, exc_info()[1]) 

    def GUI_OPAL_addToServerList(self, *arg):
        def _closewin(result=None):
            dialog.deactivate()


        def addNewServer():
            def _closeprompt(result=None):
                link = prompt.get().strip()
                prompt.deactivate()
                if link == '':
                    return
                if validateWebLink(link):
                    # add to static list
                    if self.addNewServerStatic(link):
                        # add to server list
                        serverwidget.insert(END,link)
                        self.GUI_OPAL_update_server_pulldown()
                else:
                    showerror('Invalid OPAL server address', ('The link entered is not correct,'
                    ' please correct it and be sure that it contains the \'http://...\' string.'),
                    parent=prompt.interior())
                    

            prompt = Pmw.PromptDialog(parent=dialog.interior(), label_font=self.FONTbold,
                entry_font=self.FONT, entry_bg='white', title='Add new OPAL server', 
                label_text='Enter full HTTP address of the server', entryfield_labelpos='n',
                defaultbutton=0, buttons=('OK', 'Cancel'), command = _closeprompt,
                )
            prompt.activate()

        def _del():
            sel = serverwidget.curselection()
            server = serverwidget.get(sel)
            if not askyesno("Removing server...", 
                ('The server address\n\n"%s"\n\nis going to be removed.\n\nConfirm?'% server)):
                return
            self.removeServerFromFile(server)
            serverwidget.delete(sel)
            self.OPAL_servers_list.remove(server)
            self.GUI_OPAL_update_server_pulldown()


        dialog = Pmw.Dialog(parent=self.root, buttons = ('Close',), defaultbutton='Close',
            title = 'Service manager', command=_closewin,
            hull_width=600)



        listframe = Pmw.Group(dialog.interior(), tag_text = "Known services list", tag_font=self.FONTbold)

        toolbar = Frame(listframe.interior())
        Button(toolbar, text='Add...', command=addNewServer, compound=LEFT,
            font=self.FONT, image=self.ICON_open_file).pack(anchor=W, side=LEFT)
        Button(toolbar, text='Remove...', command=_del, compound=LEFT,
            font=self.FONT, image=self.ICON_remove_sel).pack(anchor=W, side=LEFT)

        toolbar.pack(anchor=W,side=TOP)

        # XXX TODO Add scroller
        f = Frame(listframe.interior())
        scrollbar = Scrollbar(f, orient=VERTICAL)
        serverwidget = Listbox(f,font=self.FONTcourier,bg='white', 
            selectbackground='blue', selectforeground='white',
            yscrollcommand=scrollbar.set)
        scrollbar.config(command=serverwidget.yview)
        scrollbar.pack(side=RIGHT,fill=Y)

        serverwidget.pack(expand=1,fill='both',side=LEFT)


        # populating the current listbox
        for s in self.OPAL_servers_list:
            serverwidget.insert(END,s)

        listframe.pack(anchor=W,side=TOP, expand=1,fill='both')

        f.pack(anchor=W,side=TOP, expand=1, fill='both')


        dialog.bind('<Escape>', lambda x: _closewin('x') )


        #dialog.activate(globalMode=1, geometry = 'first+50+20')
        dialog.activate() #globalMode=1) #'centerscreenalways') #, geometry = 'first+50+20')

    def updateOpalServer(self, *arg):
        url = self.OPALurl.get()
        text = truncateName(url,lmax=50)
        self.GUI_LABEL_ServiceUri.set( text)
        self.initOPALserver()
        self.GUI_OPALrefreshLigLib()


        

##############################
### GENERATE
##############################





    def GUImakeSubmitTab(self, target):
        
        status_info = Pmw.Group(target, tag_text = "Summary", tag_font=self.FONTbold)
        si = status_info.interior()
        
        #default_value = '[ click to set ]'

        self.GUI_LABEL_ServiceUri = StringVar(value=self.def_label_value)
        self.GUI_LABEL_LigCount = StringVar(value=self.def_label_value)
        self.GUI_LABEL_RecCount = StringVar(value=self.def_label_value)
        self.GUI_LABEL_ConfigSet = StringVar(value=self.def_label_value)
        self.OPAL_useremail = StringVar(value=self.def_label_value)

        Label(si, text=" ", width=100).grid(row=1,column=0,columnspan=2,sticky=W+E)

        Label(si, text="Service URI : ", justify=RIGHT, font=self.FONTbold).grid(row=0, column=0, sticky=E)
        self.GUI_UriStatus = Label(si, textvar=self.GUI_LABEL_ServiceUri, justify=CENTER, font=self.FONT, fg='black', bg='#ff7777',width=50)
        self.GUI_UriStatus.grid(row=0, column=1, sticky=W, padx=5,pady=5)
        #print self.notebook.pagenames()
        self.GUI_UriStatus.bind('<Button-1>', lambda x : self.notebook.selectpage('Opal Setup')) 


        Label(si, text="Ligand library : ", justify=RIGHT, font=self.FONTbold).grid(row=1, column=0, sticky=E)
        self.GUI_LigStatus = Label(si, textvar=self.GUI_LABEL_LigCount, justify=CENTER, font=self.FONT, fg='black',width=50)
        self.GUI_LigStatus.grid(row=1, column=1, sticky=W, padx=5,pady=5)
        self.GUI_LigStatus.config(borderwidth=1, highlightbackground='black')
        self.GUI_LigStatus.bind('<Button-1>', lambda x : self.notebook.selectpage('Ligands')) 

        Label(si, text="Receptor accepted : ", justify=RIGHT, font=self.FONTbold).grid(row=3, column=0, sticky=E)
        self.GUI_RecStatus= Label(si, textvar=self.GUI_LABEL_RecCount, justify=LEFT, font=self.FONT, fg='black',width=50)
        self.GUI_RecStatus.grid(row=3, column=1, sticky=W, padx=5,pady=5)
        self.GUI_RecStatus.bind('<Button-1>', lambda x : self.notebook.selectpage('Receptors')) 

        Label(si, text="Configuration file : ", justify=RIGHT, font=self.FONTbold).grid(row=5, column=0, sticky=E)
        self.GUI_ConfigStatus = Label(si, textvar=self.GUI_LABEL_ConfigSet, justify=LEFT, font=self.FONT, fg='black',width=50)
        self.GUI_ConfigStatus.grid(row=5, column=1, sticky=W, padx=5,pady=5)
        self.GUI_ConfigStatus.bind('<Button-1>', lambda x : self.notebook.selectpage('Config')) 


        Button(si, text="User email : ",justify=RIGHT,font=self.FONTbold, command=self.setUserEmail).grid(row=7,column=0, sticky=E)
        #self.GUI_UseremailStatus = Entry(si, textvariable=self.OPAL_useremail,font=self.FONT,width=50, fg='black')
        self.GUI_UseremailStatus = Label(si, textvariable=self.OPAL_useremail,font=self.FONT,width=50, fg='black')
        self.GUI_UseremailStatus.bind('<Button-1>', self.setUserEmail) 
        self.GUI_UseremailStatus.grid(row=7,column=1, sticky=W, padx=5,pady=5)
        Label(si, text=" ", width=100).grid(row=14,column=0,columnspan=2,sticky=W+E)


        status_info.pack(anchor=NW, side=TOP,expand=N,fill=X)



        self.GUI_GenerateButton = Button(target, text = "Start submission...", font=self.FONTbold,
            command=self.startNewSubmission, state=DISABLED, image=self.ICON_no_go, compound=LEFT)
        self.GUI_GenerateButton.pack(anchor=N,side=TOP,expand=N,fill=X)



        submit_frame = Pmw.Group(target, tag_text="Submitted jobs", tag_font=self.FONTbold)
        f = Frame(submit_frame.interior())
        Button(f, text='Refresh all jobs',image=self.ICON_refresh, compound=LEFT,font=self.FONT, 
            command=self.refreshJobsStatus).pack(side=LEFT, anchor=W,expand=N, padx=5)
        Button(f, text='Kill selected job',image=self.ICON_stop, compound=LEFT,font=self.FONT,
            command=self.killSelectedJob).pack(side=RIGHT, anchor=E,expand=N, padx=5)
        f.pack(side=TOP, anchor=E, expand=N,fill=X)

        

        self.jobManTree = raccoonGUI_PrjManagerTree.VSresultsTree(submit_frame.interior())
        self.jobManTree.tree.bind('<Double-Button-1>', self.jobman_on_button1)
        self.jobManTree.tree.bind('<ButtonRelease-3>', self.jobman_on_button3)

        submit_frame.pack(anchor=NW,side=TOP,expand=Y,fill=BOTH)
        self.updateStatus()




    def jobman_on_button1(self,event):
        t = event.widget
        identify = t.identify(event.x, event.y)
            
        # identify might be None or look like:
        # ('item', '2', 'column', '0') or ('item', '3', 'column', '0', 'elem', 'pyelement3')

        if identify:
            try:
                item, column, element = identify[1], identify[3], identify[5]
                try:
                    self.jobManTree.tree.itemToObj[item]
                except:
                    if self.debug:
                        print "missing item, apparently...", item
                        print sys.exc_info()[1]
                    return

            except IndexError:
                pass

    def jobman_on_button3(self,event):
        t = event.widget
        identify = t.identify(event.x, event.y)
            
        # identify might be None or look like:
        # ('item', '2', 'column', '0') or ('item', '3', 'column', '0', 'elem', 'pyelement3')

        if identify:
            try:
                item, column, element = identify[1], identify[3], identify[5]
                try:
                    obj = self.jobManTree.tree.itemToObj[item]
                     
                    self.jobman_postMenu(event, obj)
                except:
                    if self.debug:
                        print "missing item, probably root", item
                        print sys.exc_info()[1]
                    return
            except IndexError:
                pass

    def jobman_postMenu(self, event, obj):
        #print "POSTING MENU"

        def _destroyer(event=None):
            #print "DESTROYER CALLED"
            if event: event.widget.unpost()

        def deleteNode(obj):
            tree = self.jobManTree.tree
            item = tree.objToItem[obj]
            if isinstance(obj, Project):
                msg = ('The project "%s" and all data contained in it ' 
                        '(experiments, virtual screenings) is going '
                        'to be deleted.\n\nContinue?\n\n') % obj.name
                title = "Delete project"
            elif isinstance(obj, Experiment):
                msg = ('The experiment "%s" and all virtual screenings' 
                        'contained in itis going '
                        'to be deleted.\n\nContinue?\n\n') % obj.name
                title = "Delete experiment"               
            elif isinstance(obj, VirtualScreening):
                msg = ('The virtual screening "%s" is going to be deleted.\n\n'
                        'Continue?\n\n') % obj.name
                title = "Delete virtual screening"   
            tree.item_delete(item)

            # issue warning
            if not askyesno(title, msg, parent = self.root):
                return
                

            vs_jobs = obj.traverseByType(VirtualScreening, [])
            for j in vs_jobs:
                if j.status == 'Running' or j.status == 'Submitted':
                    try:
                        j.kill()
                    except:
                        print "WARNING! : error trying to kill job", j.name
            obj.delete()
            self.updateJobsHistoryFile()
        

        def downloadNode(obj, force=False):
            def close(answ):
                if answ == 'Force download to all':
                    overwrite = True
                elif answ == 'Download only missing':
                    overwrite = False
                win.deactivate()

            if isinstance(obj, VirtualScreening):
                header = 'Results for this VS job have been downloaded already.\n\n'
                vs_jobs = [ obj ]
            else:
                header = 'Some of the results have been downloaded already.\n\n'

                vs_jobs = obj.traverseByType(VirtualScreening, [] )

            # check for already downloaded results
            overwrite = force
            for j in vs_jobs:
                if not j.properties['results_location'] == '':
                    msg = ('%s'
                           'Forcing download the results again could possibly overwrite\n'
                           'old data, while some of the data could not be present on\n'
                           'the server anymore.\n\nIt is possible to force the download again\n'
                           '(possibly overwriting old data) or download '
                           'only the missing ones.') % header
                    win = Pmw.Dialog(parent=self.root,
                        #label_font=self.FONTbold,
                        #font=self.FONT,
                        title='Warning',
                        #label_text=msg,
                        defaultbutton=0,
                        buttons=('Download only missing', 'Force donwload to all', 'Cancel'),
                        command=close)
                    Label(win.interior(), text=msg, justify='left').pack(ipadx=3,ipady=3)
                    win.activate()
                    if not overwrite: return 
                    break
            count = 0
            problematic = []
            for j in vs_jobs:
                if j.status == 'Successful':
                    j_fullname = j.getfullname()
                    outdir = [ self.RESULTS_LOCATION ] + j_fullname
                    outdir = os.sep.join(outdir)
                    if 1: #try:
                        if not os.path.exists(outdir):
                            os.makedirs(outdir, 0755)
                        elif not overwrite:
                            if self.debug: print "Warning: dir[%s] already exist!" % outdir

                        if self.debug: print "downloading in outdir...", outdir, 
                        j.downloadres(outdir)
                        if self.debug: print '[done], removing tar...',
                        os.remove(outdir+os.sep+'results.tar.gz')
                        if self.debug: print '[done]\n\n'
                        count += 1
                        j.properties['results_location'] = outdir
                        exp = j.parent()
                        prj = exp.parent()
                        jobdata = [prj.name, exp.name, j.name, j.date, j.url, j.status, j.jobId, j.resurl, outdir]
                        self.updateJobDataFile( jobdata )

                    else: #except:
                        err = sys.exc_info()[1]
                        problematic.append(["|".join(j_fullname), err])
            
            if len(problematic) and self.debug:
                print "\n\n[[[[[ problematic"
                for i in problematic:
                    print i

            showinfo('Download', 'downloaded %d res' % count, parent=self.root)
                
            #print "dw> called with obj", obj, obj.name
            #print "IS IT DOWNLOADED ALREADY? [%s]"% obj.properties['results_location']

            # XXX 
            # walk the tree
            # l = ( prj, exp, vs)
            # outdir = os.sep.join(l)
            # os.makedirs(outdir, 0755)
            # write this down in the history
            # VirtualScreening.properties['results_location'] = outdir
            # download the actual files

        def copyUrlNode(obj):
            url = obj.getresurl()
            if not 'http:' in url:
                title = 'Nothing to copy'
                msg = ('%s\n\nThe result directory of the job\n\n "%s"'
                       '\n\ndoes not seem to be available anymore.\n\n'
                       ) % (url, obj.name)
                showwarning( title, msg, parent=self.root)
                return
            r = self.root
            r.clipboard_clear()
            r.clipboard_append(url)
            title = 'URL copied'
            msg = "The result URL has been copied:\n\n%s" % url
            showinfo(title, msg, parent=self.root)

        def killJob(obj):
            if isinstance(obj, VirtualScreening):
                vs_jobs = [ obj ]
            else:
                vs_jobs = obj.traverseByType(VirtualScreening, [] )
            to_kill = []
            for j in vs_jobs:
                if 'Running' in j.status:
                    to_kill.append(j)
            if len(to_kill) == 0:
                return
            title = 'Warning'
            msg = ('%d jobs are going to be killed.\n\n'
                   'Continue?') % len(to_kill)
            if not askyesno(title, msg, parent=self.root):
                return
            for j in to_kill:
                j.kill()
                self.refreshJobsStatus(obj)

        delete_cb = CallbackFunction(deleteNode, obj) #, self.jobManTree)
        update_cb = CallbackFunction(self.refreshJobsStatus, obj)
        download_cb = CallbackFunction(downloadNode, obj)
        downloadforce_cb = CallbackFunction(downloadNode, obj, force=True)
        copyurl_cb = CallbackFunction(copyUrlNode, obj)
        kill_cb = CallbackFunction(killJob, obj)
        def cb(): pass

            
        Research = raccoonGUI_PrjManagerTree.Project
        Project = raccoonGUI_PrjManagerTree.Project
        Experiment = raccoonGUI_PrjManagerTree.Experiment
        VirtualScreening = raccoonGUI_PrjManagerTree.VirtualScreening

        menu = Menu(tearoff=False)

        if isinstance(obj, VirtualScreening):
            menu.add_command(label='        Virtual screening         ', state='disable', font=self.FONTbold)
            menu.add_separator()
            menu.add_command(label='  Update status', command=update_cb, font= self.FONT)
            menu.add_command(label='  Copy results URL', command=copyurl_cb,  font=self.FONT)
            if obj.status == 'Successful':
                state='normal'
            else:
                state='disable'
            if obj.properties['results_location'] == '':
                menu.add_command(label='  Download results', state = state,
                    command=download_cb, font= self.FONT)
            else:
                menu.add_command(label='  Download results again', command=download_cb, font= self.FONT)
            menu.add_separator()
            if obj.status == 'Successful':
                menu.add_command(label='  Remove vs item...', command=delete_cb, font=self.FONT)
            else:
                state = 'normal'
                if not 'Running' in obj.status:
                    state = 'disabled'
                menu.add_command(label='  Kill vs...', command=kill_cb, font=self.FONT, state=state)

            menu.after(50, lambda: menu.bind('<Leave>', _destroyer) )
            menu.post(event.x_root-8, event.y_root-8)

        elif isinstance(obj, Experiment):
            menu.add_command(label='         Experiment'         , state='disable', font=self.FONTbold)
            menu.add_separator()
            menu.add_command(label='  Update status', command=update_cb, font= self.FONT)
            menu.add_command(label='  Download all completed', command=download_cb,  font=self.FONT)
            menu.add_command(label='  Download results again', command=downloadforce_cb, font= self.FONT)
            menu.add_separator()

            if obj.status == 'Successful':
                menu.add_command(label='  Remove experiment item...', command=delete_cb, font=self.FONT)
            else:
                menu.add_command(label='  Kill all vs...', command=kill_cb, font=self.FONT)
            menu.after(50, lambda: menu.bind('<Leave>', _destroyer) )
            menu.post(event.x_root-8, event.y_root-8)
        
        elif isinstance(obj, Project):
            menu.add_command(label='         Project'         , state='disable', font=self.FONTbold)
            menu.add_separator()
            menu.add_command(label='  Update status', command=update_cb, font= self.FONT)
            menu.add_command(label='  Download all completed', command=download_cb,  font=self.FONT)
            menu.add_command(label='  Download results again', command=downloadforce_cb,  font=self.FONT)
            menu.add_separator()
            menu.add_command(label='  Delete project...', command=delete_cb,  font=self.FONT)
            menu.add_command(label='  Kill all vs...', command=kill_cb,  font=self.FONT)
            menu.after(50, lambda: menu.bind('<Leave>', _destroyer) )
            menu.post(event.x_root-8, event.y_root-8)           



    def refreshJobsStatus(self, obj=None):
        """ update the status of the vs jobs
            - item must be a class of Experiment, VirtualScreening or Project
        
        
        """
        research = self.jobManTree.research
        Research = raccoonGUI_PrjManagerTree.Project
        Project = raccoonGUI_PrjManagerTree.Project
        Experiment = raccoonGUI_PrjManagerTree.Experiment
        VirtualScreening = raccoonGUI_PrjManagerTree.VirtualScreening

        to_be_updated = {}
        # find which experiment(s) must be checked
        if obj == None:
            obj = Research
        if isinstance(obj, Research):
            # everything must be updated (from the root object)
            exp_list = []
            for e in obj.traverseByType(ntype=Experiment, results=exp_list):
                to_be_updated[e] = e.children

        elif isinstance(obj, Project):
            # every experiment in the project must be updated
            #exp_list = item.children
            for e in obj.children:
                to_be_updated[e] = e.children
        elif isinstance(obj, Experiment):
            # all the vs in the experiment must be updated
            to_be_updated[obj] = obj.children
        elif isinstance(obj, VirtualScreening):
            # only the experiment containing the vs 
            # must be updated
            to_be_updated[obj.parent()] = [obj]

        for exp, jobs in to_be_updated.items():
            if self.debug: print "SSTART updating..."

            for j in jobs:
                if self.debug: print "--refreshing", j.name
                url = j.url
                status = j.status
                job = j.jobId
                if not "Successful" in status:
                    exp.status = '...checking...'
                    try:
                        server = OpalClient.OpalService(url)
                        checker = OpalClient.JobStatus(server, job)
                        jstat = checker.getStatus()
                        server_message = checker.getError()
                        #print "refreshJobStatus> ", server_message
                        try:
                            status = self.OPAL_jobstatus_table[jstat]
                            if self.debug: print ")))))))))) refreshJobsStatus> status is ", status, 
                        except:
                            status = 'UNKNOWN STATUS NUMBER [%s]' % jstat
                            if self.debug: print "UNKNOWN SERVER MESSAGE", server_message
                    except: 
                        if self.debug: print "*** ERROR! Impossible to check the status of job:", job
                        status = 'Unknown'
                    j.status = status 
                    item = self.jobManTree.tree.objToItem.get(j, None)
                    if not item == None:
                        txt = self.jobManTree._treeStyles['cell']['txt']
                        self.jobManTree.tree.itemelement_config(item, self.jobManTree.tree.columns[1], txt, text=status)
                    if 'Successful' in status:
                        try:
                            resurl = os.path.dirname(checker.getOutputFiles()[0])
                        except:
                            resurl = '[ expired data? ]'
                        j.resurl = resurl
            if len(exp.children) == 1:
                exp.status = exp.children[0].status.upper()
            else:
                succ = run = fail = 0
                for c in exp.children:
                    if c.status == 'Successful': succ += 1
                    elif c.status == 'Running': run += 1
                    elif c.status == 'Fail': fail += 1
                if succ == len(exp.children):
                    exp.status == 'Successful'
                    color =  '#33bb33'
                elif run == len(exp.children):
                    exp.status == 'Runnning'
                    color = 'orange'
                elif fail == len(exp.children):
                    exp.status == 'Failed'
                    color = 'red'
                else:
                    exp.status == 'Partial'
                    color = 'orange'
            color = 'black'

            try:
                item = self.jobManTree.tree.objToItem[exp]
                #item = self.jobManTree.tree.itemToObj[obj]
                txt = self.jobManTree._treeStyles['cell']['txt']
                #self.jobManTree._treeStyles['prj'] = { 'img' : pel_image, 'txt' : pel_text, 'style' : styleProject}
                self.jobManTree.tree.itemelement_config(item, self.jobManTree.tree.columns[1], txt, text=exp.status, fill=color)
            except:
                if self.debug:
                    print "ERROR", sys.exc_info()[1]
                    print "\n\n\nPossibly not visible... passing silently", exp.name
                    print "\n\n\n"


            self.jobManTree.tree.notify_generate('<Expand-before>', item=TkTreectrl.ROOT)
        self.updateJobsHistoryFile()

    def killSelectedJob(self, job_id=None):
        # XXX BROKEN HERE 
        try:
            sel = self.jobManTree.listbox.curselection()[0]
        except:
            if self.debug: print "killSelectedJob> no sel, return"
            return
        #print "SELECTION", sel
        # pre-update just to be sure
        self.refreshJobsStatus(job_id = sel)
        j = list(self.jobManTree.listbox.get(sel)[0])
        url = j[2]
        status = j[3]
        job = j[4]
        if status == 'Successful':
            showinfo("Job completed", "The job has not been deleted because it is completed")
            return
        elif status == 'Killed/Error':
            showinfo("\"It's dead, Jim.\"", "The job has been killed already.") # because it is completed")
            return

        if 1: # try
            msg = 'The following job is going to be killed:\n\njob_id : %s\n\ndate: %s' % (j[0], j[1])
            
            if askyesno("Killing job", msg, icon=WARNING):
                server  = OpalClient.OpalService(url)
                checker = OpalClient.JobStatus(server, job)
                if checker.isRunning():
                    checker.destroyJob()
                    status = 'Killed/Error'
            else:
                if self.debug: print "KILLING: user aborted"
        else:
            status = "Error: %s" % checker.getError()

        j[3] = status

        self.jobManTree.listbox.delete(sel)
        self.jobManTree.listbox.insert(sel, j[0], j[1], j[2], j[3], j[4], j[5])

    def OPAL_getJobOutput(self, event = None):

        def _closewin(result=None):
            dialog.deactivate()

        def _setoutdir(event=None):
            out_dir = askdirectory(parent=dialog.interior(), 
                title='Select the directory where to save results', initialdir=os.getcwd() )
            if not len(out_dir):
                return
            if not os.path.exists(out_dir):
                if askyesno("New directory", "The directory doesn't exist.\n\nDo you want to create it?", 
                    parent=dialog.interior(), icon=INFO):
                    os.makedirs(out_dir, 0755)
            if self.debug: print "SELECTED DIR",out_dir
            try:
                checker.downloadOutput(out_dir)
                showinfo('Download completed', 'Output files have been saved',
                    parent=dialog.interior(), )
                _closewin()
            except:
                msg = "An error occurred when downloading the output package file:\n\n%s\n\nTry to access the remote output dir to check the files." % (exc_info()[1])
                showwarning('Download error', msg, parent=dialog.interior(), )

        def _copyURL():
            lk.config(state=NORMAL)
            lk.copy()
            lk.config(state=DISABLED)
            showinfo('URL copied', 'Remote directory URL copied in the clipboard')

        try:
            sel = self.jobManTree.listbox.curselection()[0]
        except:
            return
        job_data = self.jobManTree.listbox.get(sel)[0]
        jobname = job_data[0]
        date = job_data[1]
        server = job_data[2]
        status = job_data[3]
        job = job_data[4]
        server  = OpalClient.OpalService(server)
        checker = OpalClient.JobStatus(server, job)
        outputURL = checker.getBaseURL()
    
        if checker.isRunning():
            title = "Running Job"
            msg = "The job is still running.\n Partial results (if any) can be accessed at the remote output directory."
            status = "Running"

        elif checker.isSuccessful():
            title = "Successful Job"
            msg = "The job is done. It is possible to download result files"
            status = "Successful"

        else: # FAILED/KILLED  ?
            title = "Failed/killed job"
            msg = "The job was not completed successfully.\n Partial results (if any) can be accessed at the remote output directory."
            status = "Failed/killed"


        dialog = Pmw.Dialog(parent=self.root, buttons = ('Close',), defaultbutton='Close',
        #dialog = Pmw.Dialog(parent=self.root, buttons = (),
            title = title, command=_closewin,
            hull_width=600)

        # JOB NAME
        f = Frame(dialog.interior())
        Label(f, text='Job name : ', font=self.FONTbold,width=20,height=2, 
            justify=RIGHT).grid(row=1,column=1, sticky=E, padx=3, pady=3)
        Label(f, text=jobname,justify=RIGHT,font=self.FONT,width=80, height=2,  
            borderwidth=1, relief=FLAT, highlightbackground='black', bg='white',
            highlightcolor='black', highlightthickness=1, 
            ).grid(row=1,column=2, sticky=W, padx=3,pady=3)
        #f.pack(side=TOP, expand=0, fill=BOTH)

        # DATE

        #f = Frame(dialog.interior())
        Label(f, text='Submission date : ', font=self.FONTbold,width=20,height=2, 
            justify=RIGHT).grid(row=3, column=1, sticky=W, padx=3, pady=3)
        Label(f, text=date,justify=LEFT,font=self.FONT,width=80, height=2, 
            borderwidth=1, relief=FLAT, highlightbackground='black',bg='white',
            highlightcolor='black', highlightthickness=1, 
            ).grid(row=3, column=2, sticky=E, padx=3, pady=3)

        # STATUS MESSAGE
        #f = Frame(dialog.interior())
        Label(f, text='Status : ', font=self.FONTbold,width=20,height=2, 
            justify=RIGHT).grid(row=5, column=1, sticky=W,padx=5,pady=5)
        Label(f, text=msg,justify=LEFT,font=self.FONT,width=80, height=2, 
            borderwidth=1, relief=FLAT, highlightbackground='black',bg='white',
            highlightcolor='black', highlightthickness=1, 
            ).grid(row=5,column=2, sticky=W, padx=3, pady=3)

        # OUTPUT DIR
        Label(f, text='Remote output dir. : ', font=self.FONTbold,width=20,height=2, 
            justify=RIGHT).grid(row=7, column=1, padx=3,pady=3)
        #Label(f, text=outputURL,justify=LEFT,font=self.FONT,width=80, height=2, 
        #    borderwidth=1, relief=FLAT, highlightbackground='black',
        #    highlightcolor='black', highlightthickness=1, 
        #    ).grid(row=7, column=2, padx=3, pady=3)

        lk = TextCopyPaste(f, font=self.FONT,width=80, height=2, bg='white',
            borderwidth=1, relief=FLAT, highlightbackground='black',
            highlightcolor='black', highlightthickness=1, 
            )
        lk.grid(row=7, column=2, padx=3, pady=3)
        lk.insert(END, outputURL)
        lk.configure(state=DISABLED)


        Button(f, text='COPY URL', font=self.FONT,image=self.ICON_copy,command=_copyURL).grid(row=7, column=3, padx=5,pady=3)
        f.pack(side=TOP, expand=0, padx=3,pady=3,fill='y')

    
        if status == 'Successful':
            pass
            Button(f, text='Download result files...', compound=LEFT,image=self.ICON_small_folder, font=self.FONT,
                command=_setoutdir).grid(row=10, column=1, sticky=W+E, columnspan=3)
        #outdir = os.getcwd()
        f.pack(expand=0, fill=BOTH)

        dialog.activate()


    def setUserEmail(self, askfordefault=True, parent=None, allowempty=0): #, *arg):
        
        if parent == None:
            parent = self.root
        #self.emaildefault = 'user@domain.edu'
        if validateEmail(self.OPAL_useremail.get(), localhost=False, allowempty=allowempty):
            email = self.OPAL_useremail.get()
        else:
            email = ''# 'user@domain.com'


        def close(result):
            if result=='OK':
                out = win.get()
                if validateEmail(out, exclude='user@domain.edu'):
                    # XXX transform this to be a function setting also
                    #     the default email
                    self.OPAL_useremail.set(win.get())
                    win.deactivate()
                    if makedefault.get():
                        self.writeRaccoonOpalConfig( values= { 'default_email': out } )
                    self.updateStatus()
                else:
                    showwarning('Invalid email', ('The address entered is not correct,'
                    '\n\nA correct email address should look like:\n\n'
                    '\tuser@domain.edu\n\n'), parent=win.interior())
            else:
                win.deactivate()
                self.updateStatus()

        makedefault = BooleanVar(value=False)
        win = Pmw.PromptDialog(parent=parent,
            label_font=self.FONTbold,
            entry_font=self.FONT,
            entry_bg='white',
            title='User email',
            label_text='Email used for receiving information on the submission',
            entryfield_labelpos = 'n',
            defaultbutton=0,
            buttons=('OK', 'Cancel'),
            command=close,
            hull_width=600)

        if askfordefault:
            confirm = Checkbutton(win.interior(), text = "make default", 
                variable=makedefault,font=self.FONT)
            confirm.pack(anchor=CENTER, side=TOP) #, padx=10,pady=5)
        win.insertentry((0), email)
        win.bind('<Escape>', lambda x: close('x') )
        win.activate()
    

    def updateStatus(self, *arg):
        """override the default Raccoon updateStatus function
            
        """
        c = 0

        # Uri check
        uri = self.GUI_LABEL_ServiceUri.get()
        if (not uri==self.def_label_value) and (not uri == ''):
            self.GUI_UriStatus.config(bg = '#77ff77', fg='black')
            c+=1
        else:
            self.GUI_UriStatus.config(bg = '#ff7777', fg='black')
            self.GUI_LABEL_ServiceUri.set(self.def_label_value)

        # ligand check
        lig_lib =  self.ligLibraryChoice.get()
        if not lig_lib == "":
            self.GUI_LABEL_LigCount.set(lig_lib)
            self.GUI_LigStatus.config(bg = '#77ff77', fg='black')
            c+=1
        else:
            self.GUI_LABEL_LigCount.set(self.def_label_value)
            self.GUI_LigStatus.config(bg = '#ff7777')

        # receptor check
        rec_count = len(self.RecBook.keys())
        if rec_count > 0:
            self.GUI_LABEL_RecCount.set(rec_count)
            self.GUI_RecStatus.config(bg = '#77ff77', fg='black')

            c+=1
        else:
            self.GUI_LABEL_RecCount.set(self.def_label_value)
            self.GUI_RecStatus.config(bg = '#ff7777')


        # config check
        #vals = [ self.vina_GUI_Grid_SIZE_Z, self.vina_GUI_Grid_SIZE_Z, self.vina_GUI_Grid_SIZE_Z ]
        vals = self.GUI_Grid_thumbwheel_array[3:6]
        size_count = 0
        for v in vals:
            if v.get() == 0: # the default initialization value
                break
            else:
                size_count += 1
        if size_count == 3 :
            self.GUI_LABEL_ConfigSet.set(' OK ')
            self.GUI_ConfigStatus.config(bg = '#77ff77', fg='black')

            c+=1
        else:
            self.GUI_LABEL_ConfigSet.set(self.def_label_value)
            self.GUI_ConfigStatus.config(bg = '#ff7777')

        
        if validateEmail(self.OPAL_useremail.get(), localhost=False):
            self.GUI_UseremailStatus.config(bg='#77ff77')
            c+=1
            # update the USEREMAIL COLOR
        else:
            self.OPAL_useremail.set(self.def_label_value) 
            self.GUI_UseremailStatus.config(bg='#ff7777')

        if c == 5:
            self.GUI_GenerateButton.config(state=NORMAL, image=self.ICON_go, 
                command=self.startNewSubmission)
        else:
            self.GUI_GenerateButton.config(state=DISABLED, image=self.ICON_no_go)

    def _enableSubmit(self):
        self.GUI_GenerateButton.config(state=NORMAL, image=self.ICON_go, 
            command=self.startNewSubmission)
    def _disableSubmit(self):
        self.GUI_GenerateButton.config(state=DISABLED, image=self.ICON_no_go)
        

        # update the status of the variables in Tab5

    def syncConfGUISettings(self):

        try:
            self.vina_settings['exhaustiveness'] = int(self.vina_GUI_exhaustiveness.get())
            self.vina_settings['num_modes'] = int(self.vina_GUI_numModes.get())
            self.vina_settings['energy_range'] = float(self.vina_GUI_energyRange.get())
            center = [ v.get() for v in self.GUI_Grid_thumbwheel_array[0:3] ]
            size = [ v.get() for v in self.GUI_Grid_thumbwheel_array[3:6] ]
            self.vina_settings['center_x'] = center[0]
            self.vina_settings['center_y'] = center[1]
            self.vina_settings['center_z'] = center[2]
            self.vina_settings['size_x'] = size[0]
            self.vina_settings['size_y'] = size[1]
            self.vina_settings['size_z'] = size[2]
            return True
        except:
            if self.debug: print "PROBLEM IN READING DATA FROM THE CONFIG GUI!"
            return False


    def startNewSubmission(self):

        def close(result):
            if result == 'OK':
                prj = prj_pull.getvalue()
                exp = exp_pull.getvalue()
                tag = tag_entry.getvalue()
                if prj == is_new:
                    prj = prj_new.getvalue()
                    if prj in sorted(info.keys()):
                        #prj_list:
                        msg = ('Project name: "%s"\n\nA project with this name'
                               'already exists. Do you want to append'
                               'the VS to it?') % prj
                        if not askyesno("Warning!", msg, icon=WARNING, parent=win.interior()):
                            return
                if exp == is_new:
                    exp = exp_new.getvalue()
                    if exp in _getexplist():
                        msg = ('Experiment name: "%s"\n\nA project with this name'
                               'already exists. Do you want to append'
                               'the VS to it?') % exp
                        if not askyesno("Warning!", msg, icon=WARNING, parent=win.interior()):
                            return
                
                if not prj.strip():
                   showerror('Name error', 'The project name is empty!',
                       parent=win.interior())
                   return

                if not exp.strip():
                   showerror('Name error', 'The experiment name is empty!',
                       parent=win.interior())
                   return

                    
                self.jobdata = {'prj' : prj, 'exp': exp, 'tag':tag} 
                win.deactivate()
                self.TheFunction_OPAL()
            else:
                win.deactivate()

        def _setprjname(event=None):
            choice = prj_pull.getvalue()
            if choice == is_new:
                prj_new.grid(row=4, column=2, sticky='we',padx=4,pady=4)
            else:
                prj_new.grid_forget()
            exp_list = _getexplist()
            exp_pull.setitems( exp_list )
            exp_pull.setvalue( exp_list[-1])
            exp_pull.invoke()

        def _getexplist():
            prj = prj_pull.getvalue()
            if prj == is_new:
                return [is_new]
            else:
                exp_list = sorted(info[prj].keys())
                return exp_list + [is_new]


        def _setexpname(event=None):
            choice = exp_pull.getvalue()
            if choice == is_new:
                exp_new.grid(row=8,column=2, sticky='we', padx=4,pady=4)
            else:
                exp_new.grid_forget()



        is_new = '< create new >'

        info = self.jobManTree.getTreeGraph()
        prj_list = sorted(info.keys())
        prj_list.append(is_new)

        win = Pmw.Dialog(parent=self.root, buttons=('OK', 'Cancel'),
            title = 'New virtual screening', command = close)
        w = win.interior()

        Label(w, text='Select where to archive the new VS').grid(row=0,column=1, sticky='we', columnspan=3,padx=5,pady=5)
        Frame(w,height=2,bd=1,relief=SUNKEN).grid(row=1, column=0, sticky=E+W, columnspan=3, pady=3)
        # project 
        Label(w, text='Project', font=self.FONT, width=10).grid(row=3,column=1,sticky='we')
        Label(w, text='', font=self.FONT, width=10).grid(row=4,column=1,sticky='we',pady=5) # placeholder for entry

        # spacer
        prj_pull = OptionMenuFix(w,
               menubutton_width=30,
               menubutton_font=self.FONT,
               menu_font=self.FONT,
               items = prj_list,
               initialitem=-1,
               command = _setprjname)
        prj_pull.grid(row=3,column=2,sticky='we',padx=3)

        prj_new = Pmw.EntryField(w, value='', validate = hf.validateAscii) #,
        prj_new.component('entry').configure(justify='left', font=self.FONT, bg='white',width=33)

        # --------------------------------
        Frame(w,height=2,bd=1,relief=SUNKEN).grid(row=6, column=0, sticky=E+W, columnspan=3, pady=3)
        

        # experiment
        Label(w, text='Experiment', font=self.FONT, width=10).grid(row=7,column=1,sticky='we')
        Label(w, text='', font=self.FONT, width=10).grid(row=8,column=1,sticky='we',pady=5) # placeholder for entry

        exp_pull = OptionMenuFix(w,labelpos='w',
                       menubutton_width=30,
                       menubutton_font=self.FONT,
                       menu_font=self.FONT,
                       items=[is_new],
                       initialitem=-1,
                       command = _setexpname)
        exp_pull.grid(row=7, column =2, sticky='we',padx=3)
        exp_new = Pmw.EntryField(w, value='', validate = hf.validateAscii) #,
        exp_new.component('entry').configure(justify='left', font=self.FONT, bg='white',width=30)
        _setprjname()
        prj_pull.setvalue( prj_list[-1])

        # --------------------------------
        Frame(w,height=2,bd=1,relief=SUNKEN).grid(row=9, column=0, sticky=E+W, columnspan=3, pady=3)
        # job tag 
        Label(w, text='Job name tag [optional]', font=self.FONT).grid(row=10, column=1,columnspan=3,sticky='we',padx=5)
        tag_entry = Pmw.EntryField(w, value='', validate = hf.validateAscii) #,
        tag_entry.component('entry').configure(justify='left', font=self.FONT, bg='white',width=30)
        tag_entry.grid(row=11,column=1, columnspan=3, sticky='we', padx=4,pady=4)

        win.bind('<Escape>', close)
        win.activate()




    def mergeAnalyze(self, event=None):

        def _close(event=None):
            if event == 'Stop':
                _stop()
                win.deactivate()
            else:
                _stop()
                win.deactivate(event)

        def _stop(event=None):
            self._stopvar.set(True)

        def _go():
            worst_filt = float(self.maxfilter.getvalue())
            best_filt = float(self.minfilter.getvalue())
            maxresults = int(self.maxresults.getvalue())

            total = []
            for f in self.results_DATA:
                total.extend( self.results_DATA[f] )
            # energy sorting
            self.resListContainer.listbox.delete(0,'end')
            mode = self.filterpulldown.getvalue()
            if mode == 'energy cutoff':
                field = 'energy'
            elif mode == 'l.eff. cutoff':
                field='leff'
            # sort data accordingly to field value
            total = sorted(total, key=operator.itemgetter(field))

            self._curr_data_values['best_e'] = total[0]['energy']
            self._curr_data_values['worst_e'] = total[-1]['energy']
            self._curr_data_values['best_le'] = total[0]['leff']
            self._curr_data_values['worst_le'] = total[-1]['leff']

            iter_lig_results = range(len(total))
            self._export_TOTAL = total
            self._export_MAXRES = maxresults

            if maxresults > 0 and maxresults < len(total):
                iter_lig_results = iter_lig_results[:maxresults]

            for i in iter_lig_results: #range(len(total)):
                if self._stopvar.get():
                    win.deactivate()
                    break
                win.update()
                d = total[i]
                if d[field] <= worst_filt and d[field] >= best_filt:
                    self.resListContainer.listbox.insert('end', '', '  '+str(i+1), 
                        d['name'], d['rec'], d['energy'], d['leff'], d['poses'], d['fullpath'] )
                    item = self.resListContainer.listbox.get('end')
                    if d['selected']:
                        is_selected = True
                        state = 'Checked'
                    else:
                        is_selected = False
                        state = '!Checked'
                    self.resListContainer.listbox.itemstate_forcolumn('end', 0, state)


                self._pc_var.set( percent(i, len(iter_lig_results)) )
                lab.config(text='Ligands : %d' % i)
            win.deactivate()
            self.merge_button.configure(bg=self.merge_button_default)
            return
            
        self._pc_var.set(0.0)
        self._stopvar.set(False)

        if not len(self.results_DATA):
            self._curr_data_values['best_e'] = -100.
            self._curr_data_values['worst_e'] = 0.
            self._curr_data_values['best_le'] = -100.
            self._curr_data_values['worst_le'] = 0.
            self._defaultFiltValues()
            self.resListContainer.listbox.delete(0,'end')
            return
        # check if any of the values is invalid, and exit if so
        try:
            worst_filt = float(self.maxfilter.getvalue())
            best_filt = float(self.minfilter.getvalue())
            maxresults = int(self.maxresults.getvalue())
        except:
            print "self.mergeAnalyze>_go> error"
            return

        win =  Pmw.Dialog(self.root, title='Processing', buttons=('Stop',), command=_close)
        self.root.after(50, _go)
        Label(win.interior(), text= 'Importing and combining results....',font=self.FONTbold).pack()
        lab = Label(win.interior(),text="Ligands :", font=self.FONT)
        lab.pack()
        progress = ProgressBar(master = win.interior(), variable=self._pc_var,
            w= 200, h=20, font_size=10, manager='pack')
        progress.pack(expand=0,fill='x')
        win.activate(geometry='centerscreenalways')










    def TheFunction_OPAL(self): #, generateOnly=False):
        """
            this function submit the jobs to the OPAL server
        """
        if self.debug:
            print "\n\n\n\n**********************************************"
            print "  THE FUNCTION"
            print "*******************************************\n\n\n\n"
        self._disableSubmit()
        self.syncConfGUISettings()
        # get the current data about the project
        prj = self.jobdata['prj']
        exp = self.jobdata['exp']
        tag = self.jobdata['tag']
        lig_lib = self.ligLibraryChoice.get()
        info = self.jobManTree.getTreeGraph()
        research = self.jobManTree.research

        problematic = []
        for r in self.RecBook.keys():
            if self.debug: print "Doing the test if a combination of names is already thre!"
            jobname = '%s_%s%s' % (r, lig_lib, tag )
            prj_obj = research.getChild(prj)
            if prj_obj:
                exp_obj = prj_obj.getChild(exp)
                if exp_obj:
                    if exp_obj.getChild(jobname):
                        problematic.append(jobname) 
        conflict = 'rename' # 'rename', 'overwrite'
        if len(problematic):
            msg = ( '%d name(s) already present in the results.\n\n'
                    'Some of the VS job names that are going to be generated'
                     'would overwrite previous jobs data therefore they '
                    'will be renamed automatically.\n\n'
                    'Continue?') % len(problematic)
            if not askyesno("Job naming issue", msg, parent=self.root, icon=WARNING):
                self._enableSubmit()
                return


        for r in self.RecBook.keys():

            jobname = '%s_%s%s' % (r, lig_lib, tag )
            cmdline = ""
            inFilesPath = []
            # config file
            conf = self.VinaGenConf(ligand=None, receptor=r)
            numproc = self.vina_settings['cpu']
            conf_filename = '%s_config_template.conf' % r
            writeList(conf_filename, conf, addNewLine=1)
            inFilesPath.append(conf_filename)
            cmdline += ' --config %s ' % os.path.basename(conf_filename)

            # receptor
            cmdline += ' --receptor %s ' % os.path.basename(self.RecBook[r]['filename'])
            inFilesPath.append(self.RecBook[r]['filename'])

            if self.RecBook[r]['is_flexible']:
                cmdline += ' --flex %s' %  os.path.basename(self.RecBook[r]['flex_res_file'])
                inFilesPath.append(self.RecBook[r]['flex_res_file'])

            # lig library
            cmdline += ' --ligand_db %s' % self.ligLibraryChoice.get()


            # project manager stuff
            Project = raccoonGUI_PrjManagerTree.Project
            Experiment = raccoonGUI_PrjManagerTree.Experiment
            VirtualScreening = raccoonGUI_PrjManagerTree.VirtualScreening

            p_obj = research.getChild(prj)
            if not p_obj:
                p_obj = Project(prj)
                research.addChild(p_obj)
                self.jobManTree.expandNode(research)
                
            e_obj = p_obj.getChild(exp)
            if not e_obj:
                e_obj = Experiment(exp)
                p_obj.addChild(e_obj)
                self.jobManTree.expandNode(p_obj)

            j_obj = e_obj.getChild(jobname)

            # handle homonimy
            if j_obj: 
                if conflict == 'overwrite':  # delete previous job
                    e_obj.delChild(jobname)
                elif conflict == 'rename':   # create a new valid jobname
                    c = 1
                    newname = '%s_%d' % (jobname, c)
                    while e_obj.getChild(newname):
                        c += 1
                        newname = '%s_%d' % (jobname, c)
                        if c > 99:
                            msg = ("Impossible to find an alternative name"
                                  "for job name collisions. Last string tried:\n\n"
                                  "%s\n\nSubmission aborted.") % newname
                            showerror("Name conflict problem", msg, parent=self.root, icon=ERROR)
                            return
                    jobname = newname



            #if True:
            try:
                if self.debug: print "Submitting JOB"

                sleep(3)
                submission = self.OpalService.launchJobNB(commandline=cmdline, inFilesPath=inFilesPath, 
                        numProcs = numproc, email= self.OPAL_useremail.get(), passwd = None)
                if self.debug: print "submitted"


                # date
                now = datetime.datetime.now()
                curr_date = "%02d/%02d/%d %02d:%02d:%02d" % ( now.month, now.day, now.year, now.hour, now.minute, now.second)

                jstat = submission.getStatus()
                try:
                    status = self.OPAL_jobstatus_table[jstat]
                except:
                    status = 'UNKNOWN [%s]' % jstat

                
                job = VirtualScreening(name = jobname, date=curr_date, url=self.OPALurl.get(),  
                                        status=status, jobId=submission.jobID, resurl='[ none ]')
                job.properties['job_type'] = 'opal'
                job.properties['lig_library'] = lig_lib
                job.properties['submission_date'] = lig_lib
                job.properties['receptor'] = r


                e_obj.addChild(job)
                info = (prj, exp, jobname, curr_date, self.OPALurl.get() , 
                    status, submission.jobID, '[ none ]')

                self.writeJobsStatusFile( [ info ], mode = 'a' )
                self.jobManTree.expandNode(e_obj)
            except:
                print "##########################"
                print "# A FATAL ERROR CATCHED #"
                print "##########################"

                print "==========================="
                print "FILES:"
                for f in inFilesPath:
                    print " - %s" % f
                print "==========================="
                print "CMDLINE: [%s]" % cmdline
                print "==========================="


    def _defaultFiltValues(self, event=None):
        
        filt_type = self.filterpulldown.getvalue()

        if filt_type == 'energy cutoff':
            self.maxfilter.setentry(self._curr_data_values['worst_e']+0.1)
            self.minfilter.setentry(self._curr_data_values['best_e']-0.1)

        elif filt_type == 'l.eff. cutoff':
            self.maxfilter.setentry(self._curr_data_values['worst_le']-0.01)
            self.minfilter.setentry(self._curr_data_values['best_le']-0.01)







    def GUImakeAnalysisTab(self, target):


        self.results_importedList = [] # list of items that go in "Completed Jobs"
        self.results_DATA = {}
        self.results_DATALOOKUP = {}

        # viewer initialization
        self._curr_lig = None # [ l_fullpath, l_mol ] 
        self._curr_rec = None # [ l_fullpath, l_mol ] 
        self._curr_lig_visible = None



        self._pc_var = DoubleVar(value=0.)
        self._stopvar = BooleanVar(value=False)

        self._curr_data_values = {'best_e' : 0.0, 'worst_e': 0.0 ,
                                  'best_le':0.0, 'worst_le': 0.0 }

        def _addJobs(event=None):
            title = 'Select log file to import'
            filetypes = [("OPAL screening log file", (self.RESULTFILE,), ),
                            ('Log file', ("*.log")),
                            ('Any file...', ('*.*')),
                         ]
            fname = askopenfilename(parent=self.root, title = title, filetypes = filetypes, multiple = 0)
            if not fname : return
            #print "FNAME:", fname
            self.importThisData(fname)



        def _treeDownloadedResults(event=None):
            """
            read the results file history
            build the tree with the results
            check for every VS that has .properties['results_location'] != ''
            allow to check-select items
            """
            
            self.current_results_location = self.RESULTS_LOCATION
            self._treedonwres = None

            def close(event=None):
            
                tree = self._treedownres
                if tree == None:
                    win.deactivate()
                
                if event == 'OK':
                    all_ok = 0
                    for o in tree.research.traverseByType(VirtualScreening, []):
                        if o.selected:
                            logname = os.path.join(o.path, self.RESULTFILE)
                            vs = o.name
                            exp = o.parent().name
                            prj = o.parent().parent().name
                            name = ("%s | %s | %s" % (prj, exp, vs))
                            all_ok += self.importThisData(logname, jobname=name, quiet=1)
                    self.merge_button.configure(bg='#eeaaaa')
                    if all_ok < 0:
                        showinfo("Duplicate results", "One or more results have been skipped because already imported.")
                win.deactivate()

            def setbuttons(tree):
                changedir_cb = CallbackFunction(changedir, tree)
                changedirdefault_cb = CallbackFunction(changedir, tree, self.RESULTS_LOCATION)
                b1.configure(command = changedir_cb)
                b2.configure(command = changedirdefault_cb)
                self._treedownres = tree

            def changedir(tree, newdir=None):
                if not newdir == None:
                    tree.treeObj.pack_forget()
                    self._treedownres = None
                else:
                    title = 'Select a path to scan for results...'
                    newdir = askdirectory(parent=win.interior(), title = title, mustexist=1)

                if not newdir: return
                try:
                    newdir = os.path.expanduser(newdir)
                    os.listdir(newdir)
                    self.current_results_location = newdir
                except:
                    err = sys.exc_info()[0]
                    msg = ('Error while reading the path:\n\n'
                           '%s\n\n%s') % (newdir, err)
                    showwarning('Path error', msg, parent=win.interior())
                    return
                tree.treeObj.pack_forget()
                self._treedownres = None
                pathlabel.set(hf.truncateName(newdir, 55))
                try:
                    tree = raccoonGUI_ResManagerTree.ResultsTree(win.interior(), newdir)
                    self._treedownres = tree
                    if not tree.status:
                        tree.treeObj.pack_forget()
                        self._treedownres = None
                        helplabel.pack(expand=1,fill='both',padx=5,pady=5)
                        return
                    helplabel.pack_forget()

                    setbuttons(tree) #, b1, b2)
                    tree.tree.notify_generate('<Expand-before>', item=TkTreectrl.ROOT)
                except:
                    err = sys.exc_info()[0]
                    msg = ('Error while scanning directories:\n\n'
                           '%s\n\n%s') % (newdir, err)
                    showwarning('Path error', msg, parent=win.interior())
                    helplabel.pack_forget()
                    helplabel.pack(expand=1,fill='both',padx=5,pady=5)
                    return
                print "XXX CHANGED DIR TO BE", self.current_results_location


            #==============================

            helpmsg = ( 'No virtual screening results have been found in \n'
                        'the specified directory.\n\n'
                        'Try one of the following options:\n\n' 
                        '   - select another directory with the button above\n'
                        '     or by changing the default result directory in\n'
                        '     the "File->Preferences" menu\n\n'
                        '   - submit at least a job and download the results in\n'
                        '     the default location\n\n'
                        '   - check that the virtual screening job directories\n'
                        '     contain the default summary file "screening_report.log"\n'
                        '     or use the "Import..." button to manually import a\n'
                        '     different log file.\n\n'
                        )
                

            win = Pmw.Dialog(self.root, title='Select downloaded results', buttons=('OK','Cancel'),
                command=close)
            pathlabel = StringVar(value=hf.truncateName(self.RESULTS_LOCATION, 55))

            f = Frame(win.interior() )
            b1 = Button(f, text = 'Select another directory...', image = self.ICON_open_dir,
                compound='left', height=24)
            b1.pack(anchor='w', side='left', expand=1, fill='x',padx=1, pady=1)
            b2 = Button(f, image = self.ICON_default, height=30)
            b2.pack(anchor='w', side='left',expand=0, fill='x', padx=1,pady=1)

            f.pack(anchor='n', side='top', expand=0, fill='x',padx=5, pady=1)

            Label(win.interior(), textvar = pathlabel, justify='left', highlightbackground='#aaaaaa', bg='white',
            highlightcolor='#444444', highlightthickness=1, font=self.FONT,            
            ).pack(anchor='n', side='top', expand=0,fill='x',padx=6, pady=1)

            helplabel = Label(win.interior(), text = helpmsg, justify='left')
            try:
                tree = raccoonGUI_ResManagerTree.ResultsTree(win.interior(), self.RESULTS_LOCATION)
                self._treedownres = tree
                if not tree.status:
                    tree.treeObj.pack_forget()
                    helplabel.pack(expand=1,fill='both',padx=5,pady=5)
                else:
                    tree.tree.notify_generate('<Expand-before>', item=TkTreectrl.ROOT)
            except e:
                err = sys.exc_info()[0]
                msg = ('Error while scanning directories:\n\n'
                '%s\n\n%s') % (newdir, err)
                showwarning('Path error', msg, parent=win.interior())
                self._treedownres = None
                helplabel.pack(expand=1,fill='both',padx=5,pady=5)
                return
            setbuttons(tree)
            w = win.interior()

            win.bind('<Escape>', close)
            win.activate()



        self.resviewer = Pmw.PanedWidget(self.tab6, orient='horizontal', handlesize=-1,
            separatorthickness=10, separatorrelief='raised', )


        self.resviewer.pack(expand=1,fill='both')
        self.resviewer.add('info', min=1)
        self.resviewer.add('viewer', min=1)
        handle = self.resviewer.component('handle-1')
        sep = self.resviewer.component('separator-1')

        self.resviewer.component('handle-1').place_forget()
        self.resviewer.component('handle-1').forget()
        self.resviewer.component('handle-1').pack_forget()
        self.resviewer.component('handle-1').grid_forget()
        self.resviewer.component('separator-1').configure(bd =2, #bg = '#999999'
            highlightthickness=1, highlightbackground='black', highlightcolor='black')

        # nail handle
        Frame(sep,height=40,width=4,bg='#fffeee',relief='sunken',bd=1,highlightbackground='black',
            highlightthickness=1).pack( anchor='center', 
            padx=2,pady=2,side='left',expand=0,fill=None)

        # self.ViewerInfo.pane('ligand')
        rframe = self.resviewer.pane('viewer')
        lframe = self.resviewer.pane('info')

        
        infopane = Pmw.PanedWidget(lframe, hull_borderwidth=3, separatorrelief='raised',
            separatorthickness=8, handlesize=0,orient='vertical')

        infopane.pack(expand=1,fill='both',anchor='n', side='top')


        infopane.add('joblist',min=0)
        infopane.add('reslist',min=36)

        infopane.component('separator-1').configure(bd =2,
            highlightthickness=1, highlightbackground='black', highlightcolor='black')

            #highlightbackground='black', highlightcolor='black')

        sep = infopane.component('separator-1')
        Frame(sep,height=4,width=40,bg='#fffeee',relief='sunken',bd=1,highlightbackground='black',
            highlightthickness=1).pack( anchor='center', 
            padx=2,pady=2,side='top',expand=0,fill=None)


        joblist = Pmw.Group(infopane.pane('joblist'), tag_text='Result data', tag_font=self.FONTbold)
        joblist.component('hull').configure(relief='raised')
        bframe = Frame(joblist.interior() ) # infopane.pane('joblist'))
        Button(bframe,text='Choose...',font=self.FONT, command=_treeDownloadedResults, height = 24,
            compound='left', image=self.ICON_tree).pack(side='left',anchor='w',expand=1,fill='x')
        Button(bframe,text='Import...',font=self.FONT, command=_addJobs, height = 24,
            compound='left', image=self.ICON_open_dir).pack(side='left',anchor='w',expand=1,fill='x')
        Button(bframe,text='Remove',font=self.FONT, command=self.removeJobs, height = 24,
            compound=LEFT, image=self.ICON_remove_sel).pack(side='left',anchor='w',expand=1,fill='x')
        Button(bframe,text='Remove all',font=self.FONT, command= lambda : self.removeJobs(nuke=1), height = 24,
            compound=LEFT, image=self.ICON_remove_all).pack(side='left',anchor='w',expand=1,fill='x')
        
        bframe.pack(expand=0,fill='x',anchor='n', side='top')
       # Button(joblist.interior(),text='Merge & analyze',font=self.FONT, command = self.mergeAnalyze,
       #     compound='left', image=self.ICON_merge).pack(side='bottom',anchor='s',expand=0,fill='x')
        self.jobsAnalysisListContainer = TkTreectrl.ScrolledMultiListbox(joblist.interior(), bd=2)
        self.jobsAnalysisListContainer.listbox.config(bg='white', fg='black', font=self.FONT,
            columns = ('job_name', 'receptor', '# ligands', 'summary file'), expandcolumns=(0,)) #, selectmode='extended')


        joblist.pack(side='top', anchor='w', expand=1, fill='both', pady=3, ipadx=3, ipady=3)
        #filtframe = Pmw.Group(joblist.interior(), tag_text='Filter & process',
        #                tag_font=self.FONTbold)
        filtframe = Frame(joblist.interior(),relief='sunken')


        # XXX custimozation of the tag

        #filtframe.component('tag').configure(
        #                        bd=1,highlightbackground='black', #bg='#ffffff',
        #                        compound='left', text='Results', image=self.ICON_remove_sel,
        #                                #highlightthickness=1,
        #                                )

        self.filterpulldown = OptionMenuFix(filtframe, #.interior(), 
                                labelpos='w',
                                #items_font=self.FONT,
                                #label_text='filter :',
                                #label_font=self.FONT,
                                menubutton_width=12,
                                menubutton_font=self.FONT,
                                menu_font=self.FONT,
                                items = ['energy cutoff', 'l.eff. cutoff'],
                                command=self._filter_mode_change,
                                )
        self.filterpulldown.grid(row=1,column=0,sticky=W)

        Label(filtframe, # .interior(),
            text='best', font=self.FONTbold, padx=0, pady=0).grid(row=0,column=1, sticky=W+E+N,pady=0)
        Label(filtframe, # .interior(),
            text='worst', font=self.FONTbold, padx=0, pady=0).grid(row=0,column=2, sticky=W+E+N,pady=0)
        Button(filtframe, #.interior(),
            text='default', image=self.ICON_default,
            command=self._defaultFiltValues).grid(row=1, column=3, sticky=W+E,pady=0)

        # min property filter
        #self.minfilter = Entry(filtframe.interior(), width=7, justify=RIGHT,bg='white')
        self.minfilter = Pmw.EntryField(filtframe, # .interior(), 
            value='-100', validate = {'validator' : 'real'})
        self.minfilter.component('entry').configure(justify='right', font=self.FONT, bg='white',width=8)
        self.minfilter.grid(row=1,column=1, sticky=W+E)
        
        # max property filter
        #self.maxfilter = Entry(filtframe.interior(), width=7, justify=RIGHT,bg='white')
        self.maxfilter = Pmw.EntryField(filtframe, #.interior(), 
            value='0', validate = {'validator' : 'real'})
        self.maxfilter.component('entry').configure(justify='right', font=self.FONT, bg='white',width=8)
        self.maxfilter.grid(row=1,column=2, sticky=W+E)



        Label(filtframe, #.interior(), 
            text='max.# results',font=self.FONT,
            # highlightthickness=2,bd=2,highlightcolor='black',
            ).grid(row=2, column=0,sticky='ew')
        #self.maxresults = Entry(filtframe.interior(), width=7, justify='right', bg='white')

        # max results filter
        self.maxresults = Pmw.EntryField(filtframe, command= self.mergeAnalyze,
            value=self.MAX_RESULTS, validate = hf.validatePosInt) #{'validator' : 'integer'},)
        self.maxresults.component('entry').configure(justify='right', font=self.FONT,
            bg='white',width=8)
        self.maxresults.grid(row=2,column=1,sticky='we')
        # 
        self.merge_button = Button(filtframe, #.interior(),
            text='Analyze',font=self.FONT, command = self.mergeAnalyze,
            compound='right', image=self.ICON_merge)
        self.merge_button.grid(row=1, column=4,sticky='ENS', rowspan=2,padx=5)
        self.merge_button_default = self.merge_button.config()['background'][-1] # unique uglyness...


        filtframe.pack(side='bottom', anchor='s', expand=0,fill='x',pady=3)
        self.jobsAnalysisListContainer.pack(side='bottom', fill='both', expand=1, anchor='n',pady=0)

        self.resListContainer = TkTreectrl.ScrolledMultiListbox(infopane.pane('reslist'), bd=2)
        self.resListContainer.listbox.config(bg='white', fg='black', font=self.FONT,
                    columns = ('sel', 'rank', 'ligand', 'receptor', 'energy', 'l.eff.', 'poses', 'filename' ),
                    #selectcmd = _callback,
                                )

        self.resListContainer.listbox.unbind('<Button-1>')
        self.resListContainer.listbox.unbind('<ButtonRelease-1>')
        self.resListContainer.listbox.unbind('<Double-Button-1>')
        self.resListContainer.listbox.unbind('<Key-Return>')

        
        # XXX Export button
        Button(infopane.pane('reslist'), text='Export...', font=self.FONT, #height=2,
            image=self.ICON_save, compound='left',
            command=self._exportSelRes).pack(expand=0,fill=None, anchor='e', side='bottom')

        self.resListContainer.pack(expand=1,fill='both',anchor='n',pady=4)

        lbox = self.resListContainer.listbox
        lbox.state_define('Checked')
        lbox.icons = {}
        
        checkedIcon = lbox.icons['checkedIcon'] = \
            PhotoImage(master=infopane.pane('reslist'), 
            data=('R0lGODlhDQANABEAACwAAAAADQANAIEAAAB/f3/f39',
                   '////8CJ4yPNgHtLxYYtNbIbJ146jZ0gzeCIuhQ53N',
                   'JVNpmryZqsYDnemT3BQA7'))
        unCheckedIcon = lbox.icons['unCheckedIcon'] = \
            PhotoImage(master=infopane.pane('reslist'), 
            data=('R0lGODlhDQANABEAACwAAAAADQANAI',
            'EAAAB/f3/f39////8CIYyPNgHtLxYYtNbIrMZTX+l9WThwZAmSppqGmADHcnRaBQA7'))

        el_image = lbox.element_create(type='image', image=(
            checkedIcon, 'Checked', unCheckedIcon, ()))
        styleCheckbox = lbox.style_create()
        lbox.style_elements(styleCheckbox, lbox.element('select'), el_image, lbox.element('text'))

        lbox.style_layout(styleCheckbox, el_image, padx=9, pady=2)

        #xxx = lbox.style(lbox.column(0)) #, styleCheckbox)
        #print "CURRENT STYLE", xxx
        lbox.style(lbox.column(0), styleCheckbox)
        #print "CURRENT STYLE", dir(xxx)
        #print lbox.column(0)
        #print dir(lbox.column(0))

        colors = ('white', '#ddeeff')
        for col in range(8):
            lbox.column_configure(lbox.column(col), itembackground=colors)
        #lbox.bind('<1>', self.on_button1)
        lbox.bind('<ButtonRelease-1>', self.on_button1)
        #lbox.bind('<ButtonRelease-3>', self.on_button1)
        lbox['selectbackground'] = 'white'
        lbox['selectforeground'] = 'black'


        # right frame
        viewgroup = Pmw.Group(rframe, tag_text='3D viewer', tag_font=self.FONTbold)

        self.embeddedViewer.addCamera(viewgroup.interior(), name = 'rescam')
        res_cam = self.embeddedViewer.camByName('rescam')
        self.GUI_box3D.hiddenInCamera[res_cam] = True

        cam = self.embeddedViewer.camByName('rescam')
        cam.backgroundColor = (.6, .6, .6, 1.0)
        cam.Redraw()
        #cam = self.embeddedViewer.camByName('boxcam')
        cam.fog.Set(enabled=1)   

        name = 'Analysis'

        #self.notebook.component(name+'-tab').bind('<1>', lambda x: self.embeddedViewer.activateCam(['rescam'], only=1))
        self.notebook.component(name+'-tab').bind('<1>', lambda x: self._switchCams('rescam') )

        viewgroup.pack(expand=1,side='top',anchor='n', fill='both',padx=5)
        infopane.setnaturalsize()
        infopane.updatelayout()

    def importThisData(self, fname, jobname=None, quiet=False):
        """ import the log file summary in the session"""

        if not fname in self.results_importedList:
            path = os.path.dirname(fname)
            if jobname == None:
                jobname = os.path.basename(path)
            datalines = getLines(fname)[1:]
            ligcount = len(datalines)
            recname = datalines[1].split()[4]
            txt = "   %s   "
            self.jobsAnalysisListContainer.listbox.insert('end', txt % jobname, txt % recname, txt % ligcount, txt % fname )
            self.results_importedList.append(fname)
            self.results_DATA[fname] = []
            is_selected = False
            for l in datalines:
                l = l.split()
                #processed_file = os.path.splitext(l[5])[0] + "_Vina_VS.pdbqt"
                processed_file = l[5]
                if processed_file.startswith("./"):
                    processed_file = processed_file[2:]
                fullpath = path + os.sep + processed_file
                            # ligname, energy, leff, #poses, receptor, ligfullpath, is_selected
                lig_data =  { 'name': l[0], 
                              'energy': float(l[1]),
                              'leff': float(l[2]),
                              'poses': int(l[3]),
                              'rec': l[4],
                              'fullpath': fullpath, 
                              'selected': is_selected }
                self.results_DATA[fname].append( lig_data )
                self.results_DATALOOKUP[fullpath] = [ fname, len(self.results_DATA[fname])-1 ]
            self.merge_button.configure(bg='#eeaaaa')
            return 0
        else:
            if not quiet:
                showinfo("Duplicate results", "Selected results have been already imported.\n\n[%s]" % fname)
            return -1


        #    self.jobManTree.listbox.insert('end', info[0], info[1], info[2], info[3], info[4], info[5])

    def removeJobs(self, event=None, nuke=0):
        if not len(self.results_importedList):
            return
        if nuke:
            text = 'All results are going to be removed.\n\n Continue?'
            if not askyesno('Removing all results', text, icon=WARNING):
                return
            del self.results_importedList[:]
            self.jobsAnalysisListContainer.listbox.delete(0, 'end')
            self.resListContainer.listbox.delete(0,'end')
            self.results_DATA.clear()
        else:
            raw_sel = self.jobsAnalysisListContainer.listbox.curselection()
            if not raw_sel: return
            list_sel = map(int, raw_sel)
            self.jobsAnalysisListContainer.listbox.delete(raw_sel[0])
            list_sel.reverse()
            for s in list_sel:
                f = self.results_importedList.pop(s)
                del self.results_DATA[f]
            self.mergeAnalyze()



    def _exportSelRes(self):
        #print "_exportSelRes>"

        data = []
        def _gatherdata():

            #print "_gatherdata"

            data = []
            try:
                self._export_MAXRES
                self._export_TOTAL
            except:
                if self.debug: print "SOMETHING WRONG"
                return

            mode = sel_var.get()
            if mode == 0: # selected
                max_count = min(self._export_MAXRES, len(self._export_TOTAL) )
                also_not_selected = False
            elif mode == 1: # filtered
                max_count = min(self._export_MAXRES, len(self._export_TOTAL) )
                also_not_selected = True
            elif mode == 2: # all
                max_count = len(self._export_TOTAL)
                also_not_selected = True

            #data = []

            at_least_one = False 
            for c in range(max_count): #self._export_TOTAL:
                l = self._export_TOTAL[c]
                if l['selected'] or also_not_selected:
                    #line = "%s\t%2.3f\t%2.3f\t%d\t%s\t%s" % ( l['name'], l['energy'], l['leff'], l['poses'],
                    #    l['rec'], l['fullpath'])
                    data.append(l)
                    if not at_least_one: at_least_one = True

            if not at_least_one:
                message = ("The file cannot be saved because "
                           "no ligands are selected.\n\n"
                           "Either select one or more ligands in "
                           "the result list or specify a different"
                           "ligand set (i.e. "
                           "'Filtered' or 'All') and try again.")

                showinfo('No ligands selected', message, parent = win.interior())
                return []
            return data


        def _savelog(event=None):
            
            data = _gatherdata()
            if not len(data):
                return
            
            title = "Choose output tog filename"
            outfname = asksaveasfilename(parent=win.interior(), title = title)
            if not outfname:
                if self.debug: print "_savelog> NO FILENAME REPORTED"
                return
            outdata = ["#namet\tenergy\tligand_efficiency\ttotal_poses\treceptor\tfilename"]
            for l in data:
                line = "%s\t%2.3f\t%2.3f\t%d\t%s\t%s" % ( l['name'], l['energy'], l['leff'], l['poses'],
                        l['rec'], l['fullpath'])
                outdata.append(line)
            try:
                writeList(outfname, outdata, addNewLine=1)
            except:
                showwarning("File error", "Impossible to save the log file:\n\n %s\n" % outfname )
                return
            showinfo("Log file", "File saved successfully.", parent=self.root)

                

        def _savemols(event=None):
            if self.debug: print "_savemols"
            data = _gatherdata()
            if not len(data):
                if self.debug: print "savemols: NOTHING IN DATA", len(data)
                return
            if self.debug: print "chosedir"
            
            title = "Choose a dir where to save structures"
            outdir = askdirectory(parent=win.interior(), title = title)
            if not outdir:
                return
            if not os.path.exists(outdir):
                msg =  ("Selected directory does not "
                        "exist.\n\nCreate a new one?")
                if not askyesno('New directory', msg, icon=INFO):
                    return
                try:
                    os.makedirs(outdir, 0755)
                except:
                    error = ('An error occurred when creating '
                             'the directory:\n\n%s'
                            )
                    showerror("Creating new dir", error % outdir)
                    return
            elif len(os.listdir(outdir)) > 0:
                msg = ('The selected directory is not empty,\n'
                       'some files could get overwritten.\n\n'
                       'Continue?')
                if not askyesno('Directory not empty', msg, icon=WARNING, parent=self.root):
                    return

            reclist = []
            for l in data:
                lfile = l['fullpath'] #data['fullpath']
                fpath = os.path.dirname(lfile)
                rfile = l['rec'] # data['rec']
                if rfile in reclist:
                    rfile = None
                else:
                    reclist.append(rfile)
                    rfile = fpath+os.sep+rfile
                shutil.copy(lfile, outdir)
                if not rfile == None:
                    shutil.copy(rfile, outdir)

            showinfo("Coordinate files", "Files saved successfully.", parent=self.root)

        if not len(self.results_DATA):
            return


        win = Pmw.Dialog(self.root, title='Export data', buttons=('Close',)) #, command=_close)
        group = Pmw.Group(win.interior(), tag_text='Ligands',tag_font=self.FONTbold)
        group.grid(row=0, column=0,sticky='we',padx=5, pady=5)
        parent = group.interior()

        sel_var = IntVar(value=0) # 0: selected, 1: filtered, 2: all
        Radiobutton(parent, text='Selected', variable=sel_var, value=0).grid(row=4,column=0, sticky='w',padx=3)
        Radiobutton(parent, text='Filtered', variable=sel_var, value=1).grid(row=4,column=1, sticky='w',padx=3)
        Radiobutton(parent, text='All', variable=sel_var, value=2).grid(row=4,column=2, sticky='w',padx=3)
        parent = win.interior()

        #Label(parent, text='Log data').grid(row=0,column=0,sticky='w')
        Button(parent, text='Save log data...', compound='left', image=self.ICON_small_folder, #anchor ='w',
            justify='center', command=_savelog).grid(row=3,column=0,sticky='we',padx=3,pady=3)

        Button(parent, text='Save structure data...', compound='left', image=self.ICON_small_folder, 
            justify='left', command=_savemols).grid(row=5,column=0,sticky='we',padx=3,pady=3)

        win.winfo_toplevel().resizable(NO,NO)
        win.activate()

    def _switchCams(self, camname):
        
        # XXX XXX XXX XXX XXX XXX 
        # XXX USE THE NIGHTLY BUILD AND USE VISIBLE ON CAM FEATURE
        # XXX XXX XXX XXX XXX XXX 

        # hide extra molecules
        #"""

        res_obj = []
        box_obj = []
        if not self._curr_rec == None:
            res_obj.append( self._curr_rec[1] )
            res_obj.append( self._curr_lig[1] )
        try:
            if not len(self.CURRENT_RECEPTOR) == 0:
                box_obj.append( self.CURRENT_RECEPTOR[0] )
        except:
            pass

        if camname == 'rescam':
            to_show = res_obj
            to_hide = box_obj
        elif camname == 'boxcam':
            to_show = box_obj
            to_hide = res_obj

        for o in to_hide:
            self.molViewer.showMolecules( o, negate=1, redraw=1, log=0)
        for o in to_show:
            self.molViewer.showMolecules( o, negate=0, redraw=1, log=0)
            
            # hide result files
            #if not self._curr_lig == None:
            #    self.molViewer.showMolecules(self._curr_lig[1], negate=True, redraw=1, log=0)
            #if not self._curr_rec == None:
            #    self.molViewer.showMolecules(self._curr_lig[1], negate=True, redraw=1, log=0)
        # """     
        #print "ACTIVATING CAMERA", camname
        self.embeddedViewer.activateCam([camname], only=1)



    def on_button1(self, event):
        """ freely inspired from Pmv/autoPairAtoms.py """

        lbox = self.resListContainer.listbox
        try:
            sel = lbox.curselection()
            identify = lbox.identify(event.x, event.y)
            item = None
            if identify:
                try:
                    item, column, element = identify[1], identify[3], identify[5]
                except IndexError:
                    pass
            if item == None: return

            lbox['selectbackground'] = '#ffff00'
            values =  lbox.get(lbox.index(item=item))[0]
            molname = values[2]
            recname = values[3]
            l_fname = values[7]
            fullpath = os.path.dirname(values[7])
            r_fname = fullpath + os.sep + recname
            loup = self.results_DATALOOKUP[l_fname]
            processed_file = os.path.splitext(l_fname)[0] + "_Vina_VS.pdbqt"
            lbox.select_anchor(lbox.index(item=item))

            if int(column) == 0:
                lbox.itemstate_forcolumn(item, column, '~Checked')
                self.results_DATA[loup[0]][loup[1]]['selected'] = not self.results_DATA[loup[0]][loup[1]]['selected']
                lbox.update_idletasks()
            # loading molecule...
            self._loadMol(lig=l_fname, rec=r_fname)

        finally:
            #lbox.bind('<ButtonRelease-1>', self.on_button1)
            try:
                lbox.select_clear()
                lbox.select_set(*sel)
            except:
                pass


    def _loadMol(self, lig, rec=None):
        lbox = self.resListContainer.listbox #.unbind('<ButtonRelease-1>') #, self.on_button1)
        self._busyLoading = True
        try:
            lbox.unbind('<ButtonRelease-1>') #, self.on_button1)
            box_cam = self.embeddedViewer.camByName('boxcam')
            res_cam = self.embeddedViewer.camByName('rescam')

            rec_geom = [ 'secondarystructure', 'lines' ]
            lig_geom = [ 'sticks', 'balls', 'lines' ]

            to_delete = []
            if not self._curr_lig == None:
                if lig == self._curr_lig[0]:
                    #print "LIGAND ALREADY LOADED", lig
                    return
                else:
                    # set old lig invisible
                    self.molViewer.showMolecules(self._curr_lig[1], negate=True, redraw=1, log=0)
                    to_delete.append( self._curr_lig[1])
            #############
            # RECEPTOR

            mol = None
            if not self._curr_rec == None:
                if not os.path.basename(rec) == os.path.basename(self._curr_rec[0]):
                    # set old rec invisible
                    self.molViewer.showMolecules(self._curr_lig[1], negate=True, redraw=1, log=0)
                    to_delete.append( self._curr_rec[1] )
                    self._curr_rec = [rec, self.molViewer.readMolecule(rec,log=0)[0] ]
                    mol = self._curr_rec[1]
            else:
                self._curr_rec = [rec, self.molViewer.readMolecule(rec,log=0)[0] ]
                mol = self._curr_rec[1]


            if mol: # rec style here
                self._recStyle(mol)

            #############
            # ligand

            self._curr_lig = [lig, self.molViewer.readMolecule(lig, modelsAs='conformations', log=0)[0] ]

            # XXX DO SOME VIEWER RESETTING? 

            # lig rep
            mol = self._curr_lig[1]
            self._ligStyle(mol)


            # limit ligand visibility to rescam
            for g in mol.geomContainer.geoms.keys(): #rec_geom:
                geom = mol.geomContainer.geoms[g]
                geom.hiddenInCamera[box_cam] = True
                #mol.geomContainer.geoms['sticks'].applyStrokes()
                geom.applyStrokes()

            # rec style


            # delete old stuff
            for d in to_delete:
                self.molViewer.deleteMol(d)
        finally:
            #self._busyLoading = False
            lbox.bind('<ButtonRelease-1>', self.on_button1)


    def _recStyle(self, mol):

        self.molViewer.ribbon(mol, negate=False, only=False, redraw=1, log=1)
        #r_c_color = '#6BFF54'
        r_c_color = '#07ff11'
        #r_c_color = '#99ff99'
        #r_c_color = '#FF0000'
        r_c_color = [tuple(hex2rgb(r_c_color))]
        carbons = "%s:::C*" % mol.name
        #print "=======================\n\n\n\n"
        #print "MOLNAME", mol.name, r_c_color
        # lines
        #print "COLORING BY FLAT"
        #self.molViewer.color(mol, r_c_color, redraw=1, log=0)
        #self.molViewer.colorByAtomType(mol, ['lines',], redraw=1, log=0)
        #print carbons
        self.molViewer.color(carbons,   r_c_color, redraw=1, log=0) 
        #self.molViewer.color(carbons, ['lines',],  r_c_color, redraw=1, log=0)

        #print "COLOR BY CUSTOM", r_c_color

        # NOTE sec structure strokes
        #mol.geomContainer.geoms['secondarystructure'].applyStrokes()

        # sec.structure
        #text = """self.molViewer.color(mol,['secondarystructure',],  r_c_color, redraw=1, log=0)"""
        #print "THIS IS THE COMMAND:\n", text
        #exec(text)
        # XXX THIS DOESNT WORK
        """
        geoms = [ x.name for x in mol.geomContainer.geoms['secondarystructure'].children ]
        print geoms
        self.molViewer.color(mol, geoms, r_c_color, redraw=1, log=0)
        #self.molViewer.color(mol.name,['secondarystructure'],  r_c_color, redraw=1, log=0)


        for g in mol.geomContainer.geoms.keys(): #rec_geom:
            geom = mol.geomContainer.geoms[g]
            geom.hiddenInCamera[box_cam] = True

            #mol.geomContainer.geoms['sticks'].applyStrokes()
        """
                        


    def _ligStyle(self, mol):
        self.molViewer.displaySticksAndBalls( mol,
                       log=0, sticksBallsLicorice='Licorice',
                       cradius=0.2, bRad=0.3, negate=False,
                       bScale=0.0, redraw=True)            
        # lig color
        l_c_color = '#6BFF54'
        l_c_color = '#ffff00'
        l_c_color = [hex2rgb(l_c_color)]
        #self.molViewer.colorByAtomType(mol, redraw=1, log=0)
        carbons = "%s:::C*" % mol.name
        self.molViewer.color(carbons, l_c_color, log=0)




    def _filter_mode_change(self, event=None):
        self._defaultFiltValues() 
        self.filterResults()

    def filterResults(self,event=None):
        if self.debug:
            print "CRITERION:",self.filterpulldown.getvalue()
            print "MIN:",self.minfilter.get()
            print "MAX:",self.maxfilter.get()
    



if __name__ == '__main__':
    import sys
    from Tkinter import *
    root = Tk()
    rac = RaccoonOpalGUI(root=root, debug=True, local_testing=0)
    print sys.argv
    if len(sys.argv) > 1: 
        for i in sys.argv:
            if i == '-i':
                print "INTERACTIVE"

                sys.stdin = sys.__stdin__
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                #print "HERE", rac
                import code
                try: # hack to really exit code.interact 
                    mod = __import__('__main__')
                    code.interact( 'Pmv Interactive Shell', local=mod.__dict__)
                except:
                    pass
    else:
        print "AUTO"
        root.mainloop()   #root.mainloop()
