#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2013
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/fileCmdsProxy.py,v 1.1 2014/05/16 23:20:32 annao Exp $
#
# $Id: fileCmdsProxy.py,v 1.1 2014/05/16 23:20:32 annao Exp $
#


def getGUI(GUITK):
    if GUITK=='Tk':
        from guiTK.fileCmds import ReadMoleculesMenuGUI, PDBWriterGUI, ReadAnyGUI,\
              ReadPmvSessionGUI, FetchGUI
        return {
            'readMolecules' : [(ReadMoleculesMenuGUI, (), {})],
            'writePDB':  [(PDBWriterGUI, (), {})],
            'readAny': [(ReadAnyGUI, (), {})],
            'readPmvSession':[(ReadPmvSessionGUI, (), {})],
            'fetch': [(FetchGUI, (), {})]
            }

    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {'readMolecules' : [(None , (), {})],
                'writePDB': [(None , (), {})],
                'readAny': [(None , (), {})],
                'readPmvSession': [(None , (), {})],
                'fetch': [(None , (), {})]
                 }
    
    

commandsInfo = {
    'icoms' : {
        }
    }
