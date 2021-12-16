#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2013
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/deleteCmdsProxy.py,v 1.1 2014/05/28 23:12:18 annao Exp $
#
# $Id: deleteCmdsProxy.py,v 1.1 2014/05/28 23:12:18 annao Exp $
#

def getGUI(GUITK):
    if GUITK=='Tk':
        from guiTK.deleteCmds import DeleteMoleculesGUI, DeleteAllMoleculesGUI,\
              DeleteCurrentSelectionGUI, DeleteHydrogensGUI
        return {
            'deleteMol':[(None , (), {})],
            'deleteMolecules':[(DeleteMoleculesGUI , (), {})],
            'deleteAllMolecules' : [(DeleteAllMoleculesGUI , (), {})],
            'deleteAtomSet':[(None , (), {})],
            'deleteCurrentSelection' :[(DeleteCurrentSelectionGUI , (), {})],
            'deleteHydrogens':[(DeleteHydrogensGUI , (), {})],
            'restoreMol':[(None , (), {})]
            }
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {
            'deleteMol':[(None , (), {})],
            'deleteMolecules':[(None , (), {})],
            'deleteAllMolecules' : [(None , (), {})],
            'deleteAtomSet':[(None , (), {})],
            'deleteCurrentSelection' :[(None , (), {})],
            'deleteHydrogens':[(None , (), {})],
            'restoreMol':[(None , (), {})]}
    
commandsInfo = {
    'icoms' : {
        }
    }
