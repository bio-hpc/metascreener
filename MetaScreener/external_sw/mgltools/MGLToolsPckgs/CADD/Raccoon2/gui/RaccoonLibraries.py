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

import os, sys
from CADD.Raccoon2 import HelperFunctionsN3P as hf
from DebugTools import DebugObj
import threading
from datetime import datetime

class Library(DebugObj):
    """ contains and maps all the library data
    
        allows to get the list of ligands, generates
        the files for the jobs submission, does the 
        filtering on the fly...

    """

    def __init__(self, server, name = 'noname', _format = 'pdbqt', info = None, debug=False):
        DebugObj.__init__(self, debug)
        self.dprint("init class")
        self.server = server
        self.items = {}
        # NOTE this variable is set automatically 
        # by self.upload() and self._readIndex()
        self.path = None

        self.options = { 'split' : 1000, # create sub-directories each N ligs
                    }

        self.ready = False
        self.info = { 'name'   : name,
                      'count'  : 0,
                      'date'   : None,
                      'format' : _format,
                      'index_file': None,
                      'comments': "",
                      'properties' : {},
                      'type' : None,
                    }

        self.filters = {}

        if info:
            self.info = info
            # restore the library obj from an index file
            if self.info['index_file']:
                self._readIndex()


    def updatestatus(self):
        """set the .ready attribute"""
        c = (self.info['count'] > 0)
        i = (not self.info['index_file'] == None)
        self.dprint("count[%s] index[%s]" % (c, i))
        self.ready = (c and i)

    def name(self):
        """ used for sorting libraries """
        return self.info['name']

    # XXX potentially useless
    def setInfo(self, info):
        """set the library info as the dictionary provided"""
        self.info = info


    def getInfo(self, key=None):
        """retrieve all info or a specific one about the library"""
        if key == None:
            return self.info
        else:   
            return self.info[key]

    def _date(self):
        """generate date format for library info"""
        d = datetime.now()
        return [d.year, d.month, d.day, d.hour, d.minute, d.second ]

    def filterItems(self, items = [], filterset = {}):
        """return items passing filters

            a list of items can be optonally passed

            filterset is optional if self.filters is defined

         filterset = { property1 : [min, max],  ....}
        """
        if items == []:
            items == self.items.keys()
        if filterset == {}:
            filterset = self.filters

        filtered = []
        for i in items:
            accepted = True
            iprop = self.items[i]['properties']
            for f in filterset.keys():
                fmin, fmax = filterset[f]
                if not (iprop[f] >= fmin) or (iprop[f] <= fmax):
                    accepted = False
                    break
            if accepted:
                filtered.append(i)
        return filtered

    def setfilters(self, filterset = {}, dofilter=False):
        """ set the filter set to the required filterset"""
        self.filters = filterset
        if self.dofilter:
            return self.filterItems()

    def delfilters(self):
        """ remove all filters"""
        self.filters = {}

    def _checkitem(self, item, dup = 'rename'):
        """ check if item is already registered and 
            provide fallback options for the naming
            scheme:

                dup = 'overwrite'  duplicates not allowed (last kept)
                dup = 'rename'     duplicates renamed
                dup = 'skip'       duplicates not allowed (first kept)
        """
        name,ext = os.path.splitext(item)
        name = os.path.basename(name)
        # manage ligand name
        if self.items.get(name):
            self.dprint("ligand with same name found")
            if dup == 'rename':
                self.dprint("duplicates will be RENAMED")
                new_name = name
                count = 0
                while new_name in self.items.keys():
                    count += 1
                    new_name = new_name+"_%d" % count
                name = new_name
            elif dup == 'overwrite':
                self.dprint("duplicates will be OVEWRITTEN")
                pass
            elif dup == 'skip':
                self.dprint("duplicates will be SKIPPED")
                return False
        else:
            self.dprint("new item")
        destname = name+ext
        return name, destname

    def _additems(self, items, propfunc=None, dup = 'rename', stopcheck=None, showpercent=None, GUI=None):
        """ 
            add [items] to the current item list

            propfunc    functio to be used to calculate properties

            dup = 'overwrite'  duplicates not allowed (last kept)
            dup = 'rename'     duplicates renamed
            dup = 'skip'       duplicates not allowed (first kept)
        """
        self.dprint("adding [%d] items"% len(items), new=1)
        problematic = []
        c = 1
        # XXX FIXME profile here!
        for i in items:
            #source = i
            checkreport = self._checkitem(i, dup = dup)
            if checkreport:
                name, destname = checkreport
            #if self._checkitem(i):
                # manage ligand properties
                if propfunc:
                    report, prop = propfunc(i)
                else:
                    report, prop = True, {}
                if report:
                    self.items[name] = { 'source'    : i,
                                         'fullpath'  : destname, 
                                         # destname can be updated with the suffix dir for splitting
                                         'properties': prop,
                                       }
                else:
                    self.dprint("problematic item [%s] : [%s]" % (i, prop))
                    problematic.append([ i, prop ])
            c+=1
            if not stopcheck==None:
                if stopcheck():
                    self.dprint("stopcheck() requested stopping...")
                    break
            if not GUI == None:
                GUI.update()
            if not showpercent == None:
                pc = hf.percent(c, len(items) )
                showpercent(pc)
        self.updatestatus()
        return problematic

    def _delitems(self, names=[]):
        """delete items by name 
        
            THIS FUNCTION SHOULD NOT BE USED ON ITS OWN:
            THE CHILD SHOULD WRAP IT IN ITS METHOD
        """
        self.dprint("deleting [%d] items" % len(names))
        deleted = [ self.items.pop(n) for n in names ] 
        self.info['count'] =  len(self.items)
        self.updatestatus()
        return deleted


    def _writeIndex(self, fname=None):
        """build the zlib-compressed JSON index with all per-ligand info
           about the library file to fname (default is library.db)

           child objects have to implement their self.saveIndex method
           that will call this and perform any other operations
        """
        if fname == None:
            # build default with path
            if self.path == None:
                self.dprint('fname and self.path not defined, returning')
                return False
            fname = self.path + '/' + 'library.db'
        self.dprint('index file [%s]' % fname)
        self.info['index_file'] = fname
        self.updatestatus()
        #return self.server.writeJson(fname, data=self.items, compression=True)
        return self.server.writeMarshal(fname, data=self.items, compression=True)

    def _readIndex(self, fname=None):
        """
           rebuild the zlib-compressed library info from the index file
           child objects have to implement their self.loadIndex() method
           that will call this and perform any other operations
        """
        if fname == None:
            fname = self.info['index_file']
        if fname == None:
            self.dprint('index filename not defined')
            return False
        self.dprint('reading fname[%s]' % fname)
        self.path = fname.rsplit('/',1)[0]
        self.dprint('set lib path to [%s]' % self.path)
        try:
            #r = self.server.readJson(fname, compression=True)
            r = self.server.readMarshal(fname, compression=True)
        except:
            self.dprint("error in reading index file [%s] : %s" % (fname, sys.exc_info()[1]) )
            return False
        if r: 
            self.items = r
            self.dprint('data read successfully')
            #self.info['index_file'] = fname
        self.updatestatus()
        return True

    def register(self, overwrite=False):
        """ register itself in the master_index_file on the server
        """
        self.dprint("registration requested")
        if not self.ready == True:
            self.dprint('library not ready, stopping registration.')
            return False
        serverlib = self.server.properties['libraries']
        name = self.info['name']
        if self.server.getLibrary(name):
            self.dprint("name conflict found [%s]" % name)
            if not overwrite:
                self.dprint("no overwrite, RETURNING")
                return False
            else:
                self.dprint("overwriting requested")
                self.server.delLibrary(name)
        self.server.properties['libraries'].append(self)
        self.server.saveLibraryIndex()
        return True

    def unregister(self, delfiles=True):
        """remove itself from master_index_file"""
        name = self.info['name']
        self.dprint("unregistering library [%s]" % name)
        return self.server.delLibrary( name, delfiles)

    def upload(self, dirname=None, destpath=None, autoregister=False, overwrite=False, bg=False):
        """upload the library to the remote server $dest path"""
        if dirname == None:
            dirname = hf.validFilename(self.name())
        if dirname == '':
            dirname = 'libdir'
            self.dprint("warning: lib dirname empty, providing substutute [%s]" % libdir)
        if destpath == None:
            destpath == self.server.getLibraryPath()
        if (self.server == None) or (self.server == 'localhost'):
            self._localcopy( dirname, destpath, autoregister, overwrite, bg)
        else:
            self._remotecopy( dirname, destpath, autoregister, overwrite, bg)
        self.updatestatus()
            

    def _localcopy(self, dirname, destpath, autoregister=False, overwrite=False, bg=False):
        """ perform the copy on local path"""
        # XXX LOCAL XXX TODO
        # generating fullpath
        fulldirname = destpath+os.sep+dirname 
        print "I SHOULD COPY HERE", filldirname
        # check if exist
        #   check what's overwrite
        # check splitting settigs
        #   update name path
        # perform the copy
        # autoregister

    def _remotecopy(self, dirname, destpath, autoregister=False, overwrite=False, bg=True):
        """ perform the copy on remote path"""
        # generating fullpath destination dir
        self.path = destpath + '/' + dirname
        if self.server.ssh.exists(self.path):
            self.dprint('remote library dirname[%s] exist in the path[%s] => [%s]...' % (dirname, destpath, self.path))
            if not overwrite:
                self.dprint('overwrite not allowed, returning')
                return
            else:
                self.server.ssh.remove([self.path])
        # update the ligand destination with split_path
        step = self.options['split']
        items = sorted(self.items.keys())
        total = len(items)
        if (not step == None) and (step <= total):
            count = 0
            for i in items:
                self.dprint("updating splitted name [%s] =>" % self.items[i]['fullpath']),
                self.items[i]['fullpath'] = '/'.join([hf.splitdir(count, total, step),
                            self.items[i]['fullpath']])
                self.dprint("[%s]" % self.items[i]['fullpath'])
                count+=1
        transfer_list = []
        for i in items:
            dest = '/'.join([dirname, self.items[i]['fullpath'] ])
            transfer_list.append( [self.items[i]['source'], dest])
        # transfer files
        mule = self.server.transfer
        self.dprint("starting the transfer with the mule[%s]" % mule)
        mule.upload(files = transfer_list, remotedestpath=destpath, bg=bg)
        self.dprint("mule started... ongoing...")

        if autoregister:
            if not bg:
                libindex = self.path + '/' + 'library.db'
                self.saveIndex(libindex)
                self.registerLibrary(overwrite)
            else:
                print "AUTOREGISTER DISABLED! BACKGROUND UPLOAD (TO FIX)"


    def getFilesPath(self):
        """ return path where files are saved """
        if (self.server == None) or (self.server == 'localhost'):
            return os.path.dirname(self.info['index_file'])
        else:
            return self.info['index_file'].rsplit('/', 1)[0]




    def getItems(self, names=None):
        """ retrieve fullpath filenames for requested
            ligands (i.e. list of filtered files)
        """
        if names == None:
            names = self.items.keys()
        names = self.filterItems(items=names)
        libpath = self.getFilesPath()
        if (self.server == None) or (self.server == 'localhost'):
            sep = os.sep
        else:
            sep = '/'
        local_path_list = [ self.items[n]['fullpath'] for n in names ]
        full_path_list = [ libpath + sep + f for f in local_path_list ]
        return full_path_list


class LigandLibrary(Library):
    """
    """

    def __init__(self, server, name = 'liglibrary', _format='pdbqt', info=None, debug = False):
        Library.__init__(self, server, name, _format, info, debug)
        self.info['type'] = 'ligand'
        self._refreshProperties()


    def addLigands(self, ligands=[], dup='rename', stopcheck=None, showpercent=None, GUI=None): #, donevar=None, resultvar=None):
        """ 
            add [ligands] to the current list of ligands

            ligands = list_of_ligand_files

            dup = 'overwrite'  duplicates not allowed (last kept)
            dup = 'rename'     duplicates renamed
            dup = 'skip'       duplicates not allowed (first kept)
        """
        problematic = self._additems(items=ligands, propfunc=self._getligprop, dup=dup, 
            stopcheck=stopcheck, showpercent=showpercent, GUI=GUI)
        self.info['date'] = self._date()
        self._refreshProperties()
        #print "DEBUG Writing json here"
        #hf.writejson('_debug_LibItems.log', self.items)
        return problematic


    def deleteLigands(self, names):
        """delete ligands by name"""
        deleted = self._delitems(names=names)
        self._refreshProperties()
        return deleted

    def loadIndex(self, fname=None):
        """ rebuild the library obj info from the 
            saved index file (def: library.db)
        """
        self._readIndex(fname)
        self._refreshProperties()

    def saveIndex(self, fname=None):
        """ save the info about this obj 
            in the index file (def: library.db)
        """
        self._writeIndex(fname)


    def _refreshProperties(self):
        """update/initialize ligand library properties 
        
        
            TODO: create bins for properties distribution
                  similar to what zinc does
                http://zinc.docking.org/catalogs/asin
        """
        self.dprint("refreshing library properties...")
        lib_prop = {} 

        items = self.items.keys()
        self.info['count'] = len(items)
        for p in  ['heavy', 'mw', 'hba', 'hbd', 'tors']:
            values = sorted([ self.items[i]['properties'][p] for i in items ])
            try:    lib_prop[p] = [ values[0], values[-1] ]
            except: lib_prop[p] = []
        lib_prop['atypes'] = set([])
        for i in items:
            lib_prop['atypes'] = lib_prop['atypes'].union( set(self.items[i]['properties']['atypes']) )
        lib_prop['atypes'] = list(lib_prop['atypes'])

        self.info['properties'] = lib_prop
        self.dprint(" DONE ")

    def _getligprop(self, filename):
        """ calculate basic properties from PDBQT ligand
            mw, hba, hbd, heavy atoms
        """
        try:
            lines = hf.getLines(filename)
            atoms = hf.getAtoms(lines)
        except:
            return False, sys.exc_info()[1]
        if len(lines) == 0:
            return False, "empty file"
        if len(atoms) == 0:
            return False, "no atoms (INVALID FILE)"
        try:
            tors = int(lines[-1].split()[1])
        except:
            return False, "no torsions (INVALID FILE)"
        # hb
        hba, hbd = [ len(x) for x in  hf.findHbAccepDon(atoms) ]
        # atypes ( report all types with duplicates, to be used for updating lib types)
        atypes = [ x.split()[-1] for x in atoms ]
        # heavy
        heavy = len([ x for x in atypes if not x == 'HD' ])
        # mw
        mw = 0
        for a in atypes:
            mw += hf.adtypes.get( a, [None,0])[1]
        atypes = list(set(atypes)) #[ x.split()[-1] for x in atoms ]))
        return True, {'tors' : tors, 'heavy' : heavy, 'mw' : mw, 'hba' : hba, 'hbd': hbd, 'atypes': atypes }

    

class ReceptorLibrary(Library):
    """ """
    def __init__(self):
        pass

        # XXX it can provide a collection of receptor-flexres-config triplets
        # user should be able to choose if it wants to use them or not
        # provide auto-Config for blind docking? 


knownlibraries = { 'ligand' : LigandLibrary , 
                   'receptor' : ReceptorLibrary }
