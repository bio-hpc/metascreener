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

import re
import DebugTools
from itertools import groupby
import CADD.Raccoon2.HelperFunctionsN3P as hf

class FilterEngine(DebugTools.DebugObj):
    """ engine to filter results accordingly to
        selected engine and active filters
    """
    def __init__(self, app, debug=False):
        DebugTools.DebugObj.__init__(self, debug)
        self.app = app
                                                      # float(min) < float(max) always!
        self.settings = {  'filters': { 'energy' : { 'values' :[0, 1],
                                                     'cb'     : None,
                                                     'function' : self.energyFilter,
                                                   },

                                        'leff'   : { 'values' : [0, 1],
                                                     'cb'     : None,
                                                     'function' : self.leffFilter,
                                                   },

                                        'interactions' : { 'function': self.interactFilter,
                                                      'pattern' : [],
                                                    }
                                       # NOTES 
                                       # a filter is essentially defined 
                                       # by a function and a series of settings 
                                       # this function will know how to read
                                       # 
                                       # filtername : { 'function' : function,
                                       #                'filtersettings' : data
                                       #               }
                                      },

                           'pose':  'first', # first, any         
                           'order': [ 'energy', 'leff', 'interactions'],
                        }
        self.STOP = False

    def setFilters(self, filters={}):
        """ update filter settings"""
        for f, values in filters.items():
            self.settings['filters'][f].update(values)
        #print "\n=====\n", self.settings, "\n=====\n"

    def doFilter(self, cb = None):
        """
            this is the actual filter engine.
            it calls all the functions that are defined in the 
            perform the actual filtering
            countOnly=True: return the number of items passing
            cb is a function callback

        self.app.results = { 'resLogName' : { 'lig1' : 
                                        { 'data': 
                                            { 'energy': xxx, 
                                             }}
                                        { 'accepted':  [ 0, 2, 3]} # poses passing the filter
                                    }}
        """
        accepted = {'total' : [] }
        #total = []
        count = 0
        for resultName, data in self.app.results.items():
            result = data['results']
            for ligName, properties in result.items():
                ligId = (resultName, ligName)
                if self.STOP:
                    self.STOP = False
                    return False
                count += 1
                # reset ligand poses that have been accepted
                properties['accepted'] = range(len(properties['data']))
                # filter ligand with functions defined in self.settings
                #for filtName, filtData in self.settings['filters'].items():
                for filtName in self.settings['order']:
                    filtData = self.settings['filters'][filtName]
                    self.dprint("Filter [%s]: %s" % (filtName, filtData) )
                    if not filtName in accepted.keys():
                        accepted[filtName] = []
                    filtFunction = filtData['function'] 
                    if properties['accepted']:
                        properties['accepted'] = filtFunction(properties)
                    if len(properties['accepted']):
                        accepted[filtName].append(ligId)
                if len(properties['accepted']):
                    accepted['total'].append(ligId)
        if cb: cb(len(accepted['total']))
        return accepted


    def energyFilter(self, ligProperties):
        """ energy filter
            check if the energy of the ligand defined in
            ligProperties matches the requirements
            energy requirement and pose number are obtained
            from settings
        """
        # callbacks # NOTE not used for now
        e_cb =  self.settings['filters']['energy']['cb']
        # filter values
        emin, emax = self.settings['filters']['energy']['values']
        # which pose is requested
        opt = self.settings['pose']
        # gather ligand info and poses to scan
        ligInfo = ligProperties['data']
        ligAcceptedPoses = ligProperties['accepted']
        if opt == 'first':
            poses = [0]
        elif opt == 'any':
            poses = range(len( ligProperties.keys())) 
        passed = []
        for p in ligProperties['accepted']:
            if p in poses:
                e = ligInfo[p]['energy']
                if emin <= e <= emax:
                    #e_cb()
                    passed.append(p)
        return passed
    
    def leffFilter(self, ligProperties):
        """ ligand efficiency filter"""
        # callbacks # NOTE not used for now
        le_cb =  self.settings['filters']['leff']['cb']
        # filter values
        lemin, lemax = self.settings['filters']['leff']['values']
        # which pose is requested
        opt = self.settings['pose']
        # gather ligand info and poses to scan
        ligInfo = ligProperties['data']
        ligAcceptedPoses = ligProperties['accepted']
        if opt == 'first':
            poses = [0]
        elif opt == 'any':
            poses = range(len( ligProperties.keys())) 
        passed = []
        for p in ligProperties['accepted']:
            if p in poses:
                le = ligInfo[p]['leff']
                if lemin <= le <= lemax:
                    #e_cb()
                    passed.append(p)
        return passed


    def interactFilter(self, ligProperties):
        """ interaction filter """
        settings = self.settings['filters']['interactions']
        requested = settings['pattern']
        mode = settings['mode'] # any, all
        poses = range(len( ligProperties.keys())) 
        passed = []
        opt = self.settings['pose']
        if opt == 'first':
            poses = [0]
        # compile requested interaction patterns
        requestedInteractions = []
        for reqType in sorted(requested.keys()):
            for reqPatt in requested[reqType]:
                requestedInteractions.append( (reqType, reqPatt[0], reqPatt[1]) )
        if len(requestedInteractions) == 0:
            return poses
        for p in ligProperties['accepted']:
            if p in poses:
                interactionPool = ligProperties['data'][p]['interactions']
                satisfied = False
                for rtype, rpatt, rwanted in requestedInteractions:
                    pool = self.getUsefulInteractions(rtype, interactionPool)
                    satisfied = self.matchInteraction(rpatt, pool, rwanted)
                    if satisfied and (mode == 'any'): # one success is enough
                        break
                    elif not satisfied and (mode == 'all'): # one failure is too much
                        break
                if satisfied:
                    passed.append(p)
        return passed
 
    def getUsefulInteractions(self, rtype, interactionPool):
        """ extract useful interactions for the requested
            interaction type
        """
        pool = []
        try:
            if rtype == 'hb':   # any hb interaction, rec atom
                if 'hba' in interactionPool.keys():
                    pool += interactionPool['hba']
                if 'hbd' in interactionPool.keys():
                    pool += interactionPool['hbd']
                pool = [ x[1] for x in pool ]
            elif rtype == 'hba':   # hba, rec atom
                pool = [x[1] for x in interactionPool['hba'] ]
            elif rtype == 'hbd':   # hbd, rec atom
                pool = [x[1] for x in interactionPool['hbd'] ]
            elif rtype == 'pi':    # any pi interaction, rec atom
                if 'ppi' in interactionPool.keys():
                    pool += interactionPool['ppi']
                if 'tpi' in interactionPool.keys():
                    pool += interactionPool['tpi']
                pool = [x[0] for x in pool ]
            elif rtype == 'ppi':   # pi interaction, rec atom
                pool = [x[0] for x in interactionPool['ppi'] ]
            elif rtype == 'tpi':   # t-pi interaction, rec atom
                pool = [x[0] for x in interactionPool['tpi'] ]
            elif rtype == 'metal': # metal coordination, rec atom
                pool = [x[1] for x in interactionPool['metal'] ]
            else:  # vdw
                pool = interactionPool[rtype]
        except KeyError:
            pass
        return pool


    def matchInteraction(self, pattern, pool, wanted = True):
        """ use RE to match interactions 
            pattern : requested
            pool : pool of interactions where pattern
                              is going to be searched
            wanted: specify if the interaction is wanted or not
        """
        # B:ASN249:ND2
        pattern = pattern.replace("*", ".*")
        pattern = pattern.replace("?", ".?")
        for entry in pool:
            if re.search(pattern, entry):
                return True == wanted
        return False == wanted




