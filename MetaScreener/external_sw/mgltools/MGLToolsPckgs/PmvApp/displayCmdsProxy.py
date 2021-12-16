#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2013
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/displayCmdsProxy.py,v 1.1 2014/05/16 23:20:32 annao Exp $
#
# $Id: displayCmdsProxy.py,v 1.1 2014/05/16 23:20:32 annao Exp $
#

def getGUI(GUITK):
    if GUITK=='Tk':
        from guiTK.displayCmds import DisplayLinesGUI, DisplayCPKGUI,\
             DisplaySticksAndBallsGUI, DisplayBackboneTraceGUI, DisplayBoundGeomGUI,\
             BindGeomToMolecularFragmentGUI, ShowMoleculesGUI
        return {
            'displayLines':[(DisplayLinesGUI, (), {})],
            'undisplayLines':[(None, (), {})],
            'displayCPK': [(DisplayCPKGUI, (), {})],
            'undisplayCPK':[(None, (), {})],
            'displaySticksAndBalls':[(DisplaySticksAndBallsGUI, (), {})],
            'undisplaySticksAndBalls':[(None, (), {})],
            'displayBackboneTrace':[(DisplayBackboneTraceGUI, (), {})],
            'undisplayBackboneTrace':[(None, (), {})],
            'displayBoundGeom':[(DisplayBoundGeomGUI, (), {})],
            'undisplayBoundGeom':[(None, (), {})],
            'bindGeomToMolecularFragment':[(BindGeomToMolecularFragmentGUI, (), {})],
            'showMolecules':[(ShowMoleculesGUI, (), {})]
            }
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {'displayLines':[(None, (), {})],
                'undisplayLines':[(None, (), {})],
                'displayCPK': [(None, (), {})],
                'undisplayCPK':[(None, (), {})],
                'displaySticksAndBalls':[(None, (), {})],
                'undisplaySticksAndBalls':[(None, (), {})],
                'displayBackboneTrace':[(None, (), {})],
                'undisplayBackboneTrace':[(None, (), {})],
                'displayBoundGeom':[(None, (), {})],
                'undisplayBoundGeom':[(None, (), {})],
                'bindGeomToMolecularFragment':[(None, (), {})],
                'showMolecules':[(None, (), {})]
                }
    
commandsInfo = {
    'icoms' : {
        }
    }
