#############################################################################
#
# Author: Michel F. SANNER, , Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2014
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/editCmds.py,v 1.2 2014/07/11 05:26:11 sanner Exp $
#
# $Id: editCmds.py,v 1.2 2014/07/11 05:26:11 sanner Exp $
#
#

from PmvApp.Pmv import MVCommand

class AssignAtomsRadiiCommand(MVCommand):
    """This command adds radii to all atoms loaded in the application. Only default radii for now.
    \nPackage:PmvApp
    \nModule :editCmds
    \nClass:AssignAtomsRadiiCommand
    \nCommand:assignAtomsRadii
    \nSynopsis:\n
    None <- mv.assignAtomsRadii(nodes, united=1, overwrite=1,**kw)\n
    \nRequired Arguments:\n
    nodes --- TreeNodeSet holding the current selection
    \nOptional Arguments:\n
    \nunited   --- (default=1) flag to specify whether or not to consider
            hydrogen atoms. When hydrogen are there the atom radii
            is smaller. 

    overwrite ---(default=1) flag to specify whether or not to overwrite
            existing radii information.\n

    
    """

    def __init__(self):
        MVCommand.__init__(self)
        #self.flag = self.flag | self.objArgOnly


    def doit(self, nodes, united=True, overwrite=False):
        #nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        molecules = nodes.top.uniq()
        for mol in molecules:
            # Reassign the radii if overwrite is True
            if overwrite is True:
                mol.unitedRadii = united
                mol.defaultRadii(united=united, overwrite=overwrite)
            # Reassign the radii if different.
            elif mol.unitedRadii != united:
                mol.unitedRadii = united
                mol.defaultRadii(united=united, overwrite=overwrite)
        
    # this is done in addMolecule() of  moleculeViewer
    #def onAddObjectToViewer(self, obj):
    #    obj.unitedRadii = None
        

    def checkArguments(self, nodes, united=True, overwrite=False, **kw):
        """ None <- mv.assignAtomsRadii(nodes, united=True, overwrite=False,**kw)
        \nRequired Arguments:\n
         nodes --- TreeNodeSet holding the current selection 

         \nOptional Arguments:\n
          united --- (default=True) Boolean flag to specify whether or not
                    to consider hydrogen atoms. When hydrogen are there the
                    atom radii is smaller.\n 

          overwrite --- (default=True) Boolean flag to specify whether or not to overwrite
                    existing radii information.\n

        """
        if isinstance(nodes, str):
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.app().expandNodes(nodes)
        if not len(nodes): return (), {}
        kw = {}
        kw['united'] = united
        kw['overwrite'] = overwrite
        return (nodes, ), kw

        

commandClassFromName = {
    'assignAtomsRadii' : [AssignAtomsRadiiCommand,  None]
    }


def initModule(viewer, gui=True):
    for cmdName, values in commandClassFromName.items():
        cmdClass, guiInstance = values
        viewer.addCommand(cmdClass(), cmdName, guiInstance)
