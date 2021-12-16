#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2013
#
#############################################################################

def getGUI(GUITK):
    if GUITK=='Tk':
        return {}
#        from guiTK.displayCmds import DisplayLinesGUI, DisplayCPKGUI,\
#             DisplaySticksAndBallsGUI, DisplayBackboneTraceGUI, DisplayBoundGeomGUI,\
#             BindGeomToMolecularFragmentGUI, ShowMoleculesGUI
#        return {
#            'displayLines':[(DisplayLinesGUI, (), {})],
#            'undisplayLines':[(None, (), {})],
#            'displayCPK': [(DisplayCPKGUI, (), {})],
#            'undisplayCPK':[(None, (), {})],
#            'displaySticksAndBalls':[(DisplaySticksAndBallsGUI, (), {})],
#            'undisplaySticksAndBalls':[(None, (), {})],
#            'displayBackboneTrace':[(DisplayBackboneTraceGUI, (), {})],
#            'undisplayBackboneTrace':[(None, (), {})],
#            'displayBoundGeom':[(DisplayBoundGeomGUI, (), {})],
#            'undisplayBoundGeom':[(None, (), {})],
#            'bindGeomToMolecularFragment':[(BindGeomToMolecularFragmentGUI, (), {})],
#            'showMolecules':[(ShowMoleculesGUI, (), {})]
#            }
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {'displayHyperBalls': [(None, (), {})],
                'undisplayHyperBalls':[(None, (), {})],
                }
    
commandsInfo = {
    'icoms' : {
        }
    }
