#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2014
#
#############################################################################

# $Header: /opt/cvs/PmvApp/extrusionCmdsProxy.py,v 1.1 2014/06/27 00:08:49 annao Exp $
#
# $Id: extrusionCmdsProxy.py,v 1.1 2014/06/27 00:08:49 annao Exp $
#

def getGUI(GUITK):
    if GUITK=='Tk':
        from guiTK.extrusionCmds import ComputeSheet2DCommandGUI, Nucleic_Acids_propertiesGUI
        return {
            'computeSheet2D' : [(ComputeSheet2DCommandGUI, (), {})],
            'Nucleic_Acids_properties' : [(Nucleic_Acids_propertiesGUI, (), {})]
            }
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return { 'computeSheet2D' : [(None, (), {})],
                 'Nucleic_Acids_properties' : [(None, (), {})]}
    
commandsInfo = {
    'icoms' : {
        }
    }
