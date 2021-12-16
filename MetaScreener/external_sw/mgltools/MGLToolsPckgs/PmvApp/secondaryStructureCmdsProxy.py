#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2013
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/secondaryStructureCmdsProxy.py,v 1.1 2014/06/27 00:08:49 annao Exp $
#
# $Id: secondaryStructureCmdsProxy.py,v 1.1 2014/06/27 00:08:49 annao Exp $
#

def getGUI(GUITK):
    if GUITK=='Tk':
        from guiTK.secondaryStructureCmds import ComputeSecondaryStructureCommandGUI, \
             ExtrudeSecondaryStructureCommandGUI, \
             ExtrudeSecondaryStructureCommandUnicGUI, RibbonCommandGUI,\
             ColorBySSElementTypeGUI,  DisplayExtrudedSSCommandGUI
        return {
    'computeSecondaryStructure' : [(ComputeSecondaryStructureCommandGUI, (), {})],
    'extrudeSecondaryStructure' : [(ExtrudeSecondaryStructureCommandGUI, (), {})],
    'extrudeSecondaryStructureUnic' : [(ExtrudeSecondaryStructureCommandUnicGUI, (), {})],
    'displayExtrudedSS' : [(DisplayExtrudedSSCommandGUI, (), {})],
    'colorBySecondaryStructure' : [(ColorBySSElementTypeGUI, (), {})],
    'undisplayExtrudedSS' : [(None, (), {})],
    'ribbon' : [(RibbonCommandGUI, (), {})],
            }
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {'computeSecondaryStructure' : [(None, (), {})],
    'extrudeSecondaryStructure' : [(None, (), {})],
    'extrudeSecondaryStructureUnic' : [(None, (), {})],
    'displayExtrudedSS' : [(None, (), {})],
    'colorBySecondaryStructure' : [(None, (), {})],
    'undisplayExtrudedSS' : [(None, (), {})],
    'ribbon' : [(None, (), {})]
                }

commandsInfo = {
    'icoms' : {
        }
    }
