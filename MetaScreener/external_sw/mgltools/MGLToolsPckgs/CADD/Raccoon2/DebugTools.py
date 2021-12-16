#       
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli
#          Molecular Graphics Lab
#  
#     The Scripps Research Institute 
#           _  
#          (,)  T  h e
#         _/
#        (.)    S  c r i p p s
#          \_
#          (,)  R  e s e a r c h
#         ./  
#        ( )    I  n s t i t u t e
#         '
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import inspect
from datetime import datetime

class DebugObj:
    """
    provide basic funcionality of logging printing 
    based on debug level
    
    OPTIONS
        debug = False       : debug messages disabled
              = True        : debug messages printed on screen
              = string      : debug messages saved to filename = string

    dprint()  : debug-level dependent print function
              return the string "function [CALLER:function_caller]> message"

    TODO Add indent to show hierarchy?

    """
    def __init__(self, debug=False):

        self._dbug_spacer = "=====================================\n"
        # is a filename to open
        if type(debug) == type(''):
            bufsize = 0
            debug = open(debug, 'a', bufsize)
            debug.write("\n\n\n\n"+self._dbug_spacer+"Debug file opened on (%s)" % datetime.now())
        # it is a file pointer (nothing to do, keep going...)
        elif str(type(debug)) == "<type 'file'>":
            pass
        self.debug = debug

    def caller(self, level=1):
        #print "CALLER", inspect.stack()[1][3]
        #print "\n\n\nSTACK"
        #for i in inspect.stack():
        #    print i
        #    print "--------------"
        #print "\n++++++++++++++++++++++\n"
        try:
            return inspect.stack()[2+level][3]
        except:
            return "(unknown)"

    def dprint(self, msg, new=False, args=False):
        """this is where the magic happens"""
        if not self.debug: return
        # inspect the stack frame
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        fname = calframe[1][3]
        if args == True:
            _arg, _, _, _val = inspect.getargvalues(curframe)
            a_v = ",".join(['%s = %s' % (x, _val[x]) for x in _arg])
        else:
            a_v = ""

        # add newline if necessary
        if new == True: 
            nl = '\n\n'
        else:
            nl = ''
        # composing the message
        msg = "%sDEBUG[%s] %s(%s) [CALLER:%s()] >> %s" % (nl, datetime.now(), fname, a_v, self.caller(), msg)
        if str(type(self.debug)) == "<type 'file'>":
            self.debug.write(msg + '\n')
        else:
            print msg
