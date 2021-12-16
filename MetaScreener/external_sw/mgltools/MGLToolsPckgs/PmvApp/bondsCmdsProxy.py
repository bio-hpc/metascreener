#############################################################################
#
# Author: Michel F. SANNER,  Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2014
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/bondsCmdsProxy.py,v 1.1 2014/05/16 23:20:32 annao Exp $
#
# $Id: bondsCmdsProxy.py,v 1.1 2014/05/16 23:20:32 annao Exp $
#
#


def getGUI(GUITK):
    if GUITK=='Tk':
        from Pmv.guiTK.bondsCmds import BuildBondsByDistanceGUI,\
             AddBondsGUICommandGUI, RemoveBondsGUICommandGUI
        return {#'buildBondsByDistance' : [(BuildBondsByDistanceGUI, (), {})],
                'buildBondsByDistance' : [(None , (), {})],
                'addBonds' : [(None , (), {})],
                'addBondsGC' : [(AddBondsGUICommandGUI, (), {})],
                'removeBonds' : [(None , (), {})],
                'removeBondsGC' : [(RemoveBondsGUICommandGUI, (), {})]
            }
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {'buildBondsByDistance' : [(None , (), {})],
                'addBonds' : [(None , (), {})],
                'addBondsGC' :  [(None , (), {})],
                'removeBonds' : [(None , (), {})],
                'removeBondsGC' : [(None , (), {})]}
    
commandsInfo = {
    'icoms' : {}
    }
