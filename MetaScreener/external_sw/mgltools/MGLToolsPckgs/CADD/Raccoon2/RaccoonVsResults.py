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


import RaccoonEvents
import VsResultsGenerator
import DebugTools
import AutoDockTools.HelperFunctionsN3P as hf
import os, sys

class RaccoonVsResultsGenerator(DebugTools.DebugObj):

    def __init__(self, app, debug=False):
        DebugTools.DebugObj.__init__(self, debug)
        self.app = app
        self.processor = None
        self.app.eventManager.registerListener(RaccoonEvents.SetDockingEngine, self.setDockingEngine)

        self.settings = {'doInteractions': True, 'water_map': None, 'hbtol': 0.0 }
        self.options = {'suffix' : '.VS',   # output pdbqt+ suffix
                        'mode' : 'all',     # poses to write in log file (AD: all, le, lc; VINA: 1)
                        }
        self.receptor = None
        self.ligands = {} # { 'lig1' : [ file1.out, file2.out, ...], ... }
        self.results = {}
        # the following are used only for old text logs
        self.logHeader = { 'vina' : ('#name\tenergy\tligand_efficiency'
                                     '\ttotal_poses\treceptor\tfilename'),

                            'autodock': ('#name\tpose\tenergy\tl_efficiency'
                                         '\tclust_size\tclust_size_percent\t'
                                        'total_poses\tfilename\tis_hydrated')}
        self.setDockingEngine()

    def setDockingEngine(self, event=None):
        """ set results processor for each docking engine """
        if self.app.dockengine == 'autodock':
            self.processor = VsResultsGenerator.AutoDockVsResult
            self.dprint("dockengine => [%s]" % (self.app.dockengine))
        elif self.app.dockengine == 'vina':
            self.processor = VsResultsGenerator.AutoDockVinaVsResult
            self.dprint("dockengine => [%s]" % (self.app.dockengine))
        else:
            self.processor = None
            self.dprint("dockengine => [%s]" % None)
            print "NO ENGINE"
        if not self.processor == None:
            self.initProcessor()
            
    def initProcessor(self, receptor=None):
        """ initialize the processor"""
        #if receptor == None:
        #    if not self.receptor == None:
        #        self.dprint("no receptor defined, returning")
        #        return
        #    else:
        #        receptor = self.receptor
        self.processor = self.processor(receptor=receptor, **self.settings)
        self.results.clear()
        self.dprint("processor *READY*")

    
    def setReceptor(self, receptor):
        """ set the receptor filename used by the processor"""
        self.processor.setReceptor(receptor)
        self.results.clear()


    def generateResults(self, logfile=None, logformat='json', cb=None, stop=None):
        """ perform results generation
            logfile :   optional filename where results summary will be written
            logformat:  log format (json, txt)
            cb      :   an optional function that will be called with (name, count)
            stop    :   a boolean that will halt the process if True
        """
        c = 0
        problematic = []
        for l_name, l_files in self.ligands.items():
            #print "processing[%s]: %s" % (l_name, l_files)
            self.ligname = l_name
            # l_files can be single file or list
            self.processor.setLigands(l_files)
            c+=1
            try:
                self.processor.process()
                if cb: cb(l_name, c)
                if stop == True:
                    return
                self.writePdbqt()
                self.getResInfo()
            except:
                problematic.append([l_files, sys.exc_info()[1]])
        if logfile:
            if logformat =='json':
                self.writeLogJson(logfile)
            else:
                self.writeLog(logfile)
        return problematic
                

    def getResInfo(self):
        """ generate the info that's going to 
            be written in the log file
        """
        e = self.app.dockengine
        if e == 'autodock':
            self._getADinfo()
        elif e == 'vina':
            self._getVINAinfo()

    def _getADinfo(self):
        """ retrieve the AD log information"""
        mode == self.options['mode']
        if mode == 'le': 
            pool = [0]
        elif mode == 'lc':
            pool = [1]
            if len(self.processor.results) == 1:
                pool = [0]
        elif mode == 'all':
            pool = range(len(self.processor.results))
        if self.processor.hisHydrated:
            hydrated = '\tHYDRATED'
        #self.results[self.ligname] = {}
        data = []
        for i in pool:
            pose = self.processor.results[i]
            data.append({ 'pose'     : p+1,
                     'energy'   : pose['energy'],
                     'leff'     : pose['leff'],
                     'csize'    : pose['cpercent'],
                     'total'    : len(self.processor.poses),
                     'recname'  : self.processor.recname,
                     'pdbqt'    :  self.pdbqt_out,
                     'hydrated' : hydrated,
                     #'engine'   : 'autodock',
                    })
        accepted = range( len(self.processor.poses) )
        self.results[self.ligname] = {'data'    :data, 
                                      'accepted':accepted,
                                      'engine'  :'autodock'}

    def _getVINAinfo(self):
        """ retrieve Vina log info"""
        #self.results[self.ligname] = {}
        data = []
        data.append({ 'energy'   : self.processor.results[0]['energy'],
                 'leff'     : self.processor.results[0]['leff'],
                 'total'    : len(self.processor.poses),
                 'recname'  : self.processor.recname,
                 'pdbqt'    : self.pdbqt_out,
                 #'engine'   : 'vina',
                })
        accepted = range( len(self.processor.poses) )
        self.results[self.ligname] = {'data'    :data,
                                      'accepted':accepted,
                                      'engine'  :'vina'}

    def writePdbqt(self, path=None):
        """ save the PDBQT+ file from the current ligand"""
        pdbqt = self.processor.generatePDBQTplus()
        suffix = self.options['suffix']
        if path == None:
            path = self.processor.getPath()
        self.pdbqt_out = path + os.sep + self.ligname + suffix + '.pdbqt'
        fp = open(self.pdbqt_out, 'w')
        fp.write(pdbqt)
        fp.close()

    def writeLog(self, logname, mode='auto'):
        """ write the log of processed ligands
            in the file logname
            mode : auto      (append if exists; 
                              create new if does not)
                   overwrite (force overwrite)
        """
        e = self.app.dockengine
        data = self.logDataGen()
        if mode == 'auto':
            if os.path.isfile(logname):
                mode == 'a'
            else:
                mode == 'w'
                data = [ self.logHeader[e] ] + data
        fp = open(logname, mode)
        fp.write(data)
        fp.close()

    def writeLogJson(self, logname, compression = False):
        """ write log in json format
        """
        if not len(self.results.keys()):
            print "cowardly refusing to write an empty file"
            return
        hf.writejson(logname, self.results, compression)


    def logDataGen(self):
        """ generate the text data for the log"""
        buff = []
        e = self.app.dockengine
        if e == 'autodock':
            dataformat = ('%(pose)d\t%(energy)2.3f\t%(leff)2.3f\t'
                          '%(csize)2.1f\t%(total)d\t%(recname)s\t'
                          '%(pdbqt)s%(hydrated)s')
        elif e == 'vina':
            dataformat = ('%(energy)2.3f\t%(leff)2.3f\t%(total)d\t'
                          '%(recname)s\t%(pdbqt)s')
        for n, info in self.results.items():
            line = dataformat % info
            buff.append(n + '\t' + line)
        return buff


