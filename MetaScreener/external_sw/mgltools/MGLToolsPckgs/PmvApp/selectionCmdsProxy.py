#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2013
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/selectionCmdsProxy.py,v 1.1 2014/05/16 23:20:32 annao Exp $
#
# $Id: selectionCmdsProxy.py,v 1.1 2014/05/16 23:20:32 annao Exp $
#

def getGUI(GUITK):
    if GUITK=='Tk':
        from guiTK.selectionCmds import MVClearSelectionGUI, MVSelectSetCommandGUI,\
       MVSelectFromStringCommandGUI,  MVDirectSelectCommandGUI,\
       MVSelectSphericalRegionGUI, MVInvertSelectionGUI,\
       MVSelectNoWaterHeteroAtomsCommandGUI, MVSaveSetCommandGUI
        return {
    'select' : [(None, (), {})],
    'deselect' : [(None, (), {})],
    'clearSelection' : [(MVClearSelectionGUI, (), {})],
    'expandSelection' : [(None, (), {})],
    'selectAround' : [(None, (), {})],
    'saveSet' : [(MVSaveSetCommandGUI, (), {}) ],
    'createSetIfNeeded' : [(None, (), {})],
    'invertSelection' : [(MVInvertSelectionGUI, (), {})],
    'selectSet' : [(MVSelectSetCommandGUI, (), {})],
    'selectFromString' : [(MVSelectFromStringCommandGUI, (), {})],
    'directSelect' : [(MVDirectSelectCommandGUI, (), {})],
    'selectInSphere' : [(MVSelectSphericalRegionGUI, (), {})],
    'selectHeteroAtoms' : [(MVSelectNoWaterHeteroAtomsCommandGUI, (), {})],

}
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {
            'select' : [(None, (), {})],
            'deselect' : [(None, (), {})],
            'clearSelection' : [(None, (), {})],
            'expandSelection' : [(None, (), {})],
            'selectAround' : [(None, (), {})],
            'saveSet' : [(None, (), {})],
            'createSetIfNeeded' : [(None, (), {})],
            'invertSelection' : [(None, (), {})],
            'selectSet' : [(None, (), {})],
            'selectFromString' : [(None, (), {})],
            'directSelect' : [(None, (), {})],
            'selectInSphere' : [(None, (), {})],
            'selectHeteroAtoms' : [(None, (), {})]
            }

commandsInfo = {
    'icoms' : {
        }
    }
