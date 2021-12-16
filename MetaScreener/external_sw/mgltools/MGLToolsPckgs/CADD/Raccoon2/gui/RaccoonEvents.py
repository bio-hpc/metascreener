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

from mglutil.events import Event, EventHandler

class RaccoonEventManager(EventHandler):
    def __init__(self):
        EventHandler.__init__(self)


class SetResourceEvent(Event):
    """ class handle the resource definition/change
            [local, cluster, opal] """

    def __init__(self, resource):
        Event.__init__(self)
        self.resource = resource


class SwitchConfigCamera(Event):
    """ handle activation/deactivation of the grid box config
        camera (with preventive disactivation of other cameras?)
    """

    def __init__(self, app, is_active, *arg, **kw): # XXX remove APP
        Event.__init__(self, *arg, **kw) #
        if is_active:
            # deactivate other cameras
            # should this class be an event dispatcher?
            pass
        print "SwitchConfigCamera> [%s -> %s] "% (self.app.isConfigCameraActive, is_active)

        self.app.isConfigCameraActive = is_active


class SetDockingEngine(Event):
    """ handle selection of docking engine (AD/Vina)
    """
    def __init__(self, engine, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        self.dockingengine = engine


class SetDefaultDataPath(Event):
    """ set the default data path (i.e. from preferences)
    """
    def __init__(self, path, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        self.path = path



class SshServerManagerEvent(Event):
    """ triggered when a server is added/removed
        by the ServerManager

    """
    def __init__(self,  *arg, **kw):
        Event.__init__(self, *arg, **kw)

class ServerConnection(Event):
    """ event triggered when a connection
        is established with a server
    """
    def __init__(self,  *arg, **kw):
        Event.__init__(self, *arg, **kw)
        self.is_connected = True



class ServerDisconnection(Event):
    """ event triggered when a connection
        with a server is closed/broken
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        self.is_connected = False


class UpdateServerListEvent(Event):
    """ event triggered by a change in the list
        of known servers
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        #self.is_connected = False


class ServerFeaturesRefresh(Event):
    """ triggered when new features are added to the server
        (i.e. new libraries uploaded, new services installed
        via the GUI or by the user)
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)

class LibrariesUpdate(Event):
    """ triggered when the number of libraries on the server
        changes.
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)


class ServicesUpdate(Event):
    """ triggered when services on the server
        get installed or deleted.
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)

class ServiceSelected(Event): 
    """ triggered when selecing a service
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)


###### RECEPTOR



class ReceptorListChange(Event):
    """ triggered when new features are added to the server
        (i.e. new libraries uploaded, new services installed
        via the GUI or by the user)
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)


##### CONFIG EVENTS



class SearchConfigChange(Event):
    """ triggered when there's a change in the search configuration
        (i.e. box definition, search parm...)
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        

#### JOBS EVENTS


class UpdateJobHistory(Event):
    """ triggered when a job is submitted, or a new job history file
        is read
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        # this should be changed to be a list? prj->exp->vs
        #self.obj = kw.get('obj', None)
        self.prj = kw.get('prj', None)
        self.exp = kw.get('exp', None)
        self.name = kw.get('name', None)
        self.jtype = kw.get('jtype', None)
        self.properties = kw.get('properties', None)
        #self.status = kb['status']


class DeletedJobHystoryItem(Event):
    """ triggered when a hystory item is deleted
        the event can be defined as one of the following:
            prj, exp, vs   <-- delete vs
            prj, exp       <-- delete exp
            prj            <-- delete prj
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        # XXX see if it must be a multiple object type or only VS
        self.prj = kw.get('prj', None)
        self.exp = kw.get('exp', None)
        self.name = kw.get('name', None)
        



class SyncJobHistory(Event):
    """ triggered when connecting to a server to
        import new unknown jobs
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        
        
class UserInputRequirementUpdate(Event):
    """ triggered when user set/unset one of the requirements
        for job submission
        _type = 'ligand', 'receptor', 'config', ...
         ...???
    """
    def __init__(self, _type=None, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        self._type = _type
      

##### ANALYSIS EVENTS

class FilterSetSelection(Event):
    """ triggered when a filter set is selected
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        
class ResultsImportedDeleted(Event):
    """ triggered when results are added or removed
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)

class FilterRunEvent(Event):
    """ triggered when a filtering process is performed
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)


class FilterInteractionEvent(Event):
    """ triggered when a filtering process is performed
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)






class LigandResultPicked(Event):
    """ triggered when a filtering process is performed
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
        #print "LIGPICK", arg, kw
        self.ligname = kw['ligname']
        self.jobname = kw['jobname']
        self.pose = kw['pose']

class LigandResultNuked(Event):
    """ triggered when all ligand results are nuked
    """
    def __init__(self, *arg, **kw):
        Event.__init__(self, *arg, **kw)
