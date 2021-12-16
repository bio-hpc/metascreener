#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2014
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/msmsCmdsProxy.py,v 1.1 2014/06/06 22:44:05 annao Exp $
#
# $Id: msmsCmdsProxy.py,v 1.1 2014/06/06 22:44:05 annao Exp $
#

def getGUI(GUITK):
    if GUITK=='Tk':
        from guiTK.msmsCmds import ComputeMSMSGUI, DisplayMSMSGUI,ComputeSESAndSASAreaGUI, ReadMSMSGUI, SaveMSMSGUI
        return {
            'computeMSMS':[(ComputeMSMSGUI, (), {})],
            'displayMSMS':[(DisplayMSMSGUI, (), {})],
            'undisplayMSMS':[(None, (), {})],
            'computeSESAndSASArea':[(ComputeSESAndSASAreaGUI, (), {})],
            'readMSMS':[(ReadMSMSGUI, (), {})],
            'saveMSMS':[(SaveMSMSGUI, (), {})],
            }
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {
            'computeMSMS': [(None, (), {})],
            'displayMSMS': [(None, (), {})],
            'undisplayMSMS':[(None, (), {})],
            'computeSESAndSASArea': [(None, (), {})],
            'readMSMS': [(None, (), {})],
            'saveMSMS': [(None, (), {})],
            }    
commandsInfo = {
    'icoms' : {
        }
    }
