########################################################################
#
# Date: 2014 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################
#
# $Header: /opt/cvs/DejaVu2/Qt/EventHandler.py,v 1.1.1.1 2014/06/19 19:41:03 sanner Exp $
#
# $Id: EventHandler.py,v 1.1.1.1 2014/06/19 19:41:03 sanner Exp $
#

from DejaVu2.EventHandler import EventManagerBase

class EventManager(EventManagerBase):
    """Object used to manage callback functions for the events of a Widget

    Public Methods:
    ValideEvent(eventType)
    AddCallback(eventType, callback)
    SetCallback(func)
    RemoveCallback(eventType, func)
    ListBindings(event=None)
    """

# NOT USED, imstead I simply try to bind to a dummy widget to check if
# the given event type is valid
#
#    eventTypes = ('Key', 'KeyPress', 'KeyPress', 
#		  'Button', 'ButtonPress', 'ButtonRelease',
#		  'Enter', 'Leave', 'Motion')
#		  
#    eventModifiers = ('Control' 'Shift', 'Lock', 
#		      'Button1', 'B1', 'Button2', 'B2','Button3', 'B3',
#		      'Button4', 'B4', 'Button5', 'B5',
#		      'Any', 'Double', 'Triple',
#		      'Mod1', 'M1', 'Meta', 'M',
#		      'Mod2', 'M2', 'Alt',
#		      'Mod3', 'M3', 'Mod4', 'M4', 'Mod5', 'M5' )
#    buttonDetails = ( '1', '2', '3' )
#    keyDetails = any keysym

    def __init__(self, widget):
        EventManagerBase.__init__(self, widget)
        

    def ValidEvent(self, eventType):
	"""Check if an event is valid"""

	#try: self.dummyFrame.bind(eventType, self.DummyCallback) 
	#except: return 0
	return 1


    def AddCallback(self, eventType, callback):
	"""Add a callback fuction"""

	EventManagerBase.AddCallback(self, eventType, callback)
	self.widget.bind(eventType, callback, '+')


    def BindFuncList(self,eventType, funcList):
	"""Bind a list of functions to an event"""

	self.widget.bind(eventType, funcList[0])
	for f in funcList[1:]:
	    self.widget.bind(eventType, f, '+')
	    

    def SetCallback(self, eventType, callback):
	"""Set func as the callback or list of callback functions"""

	EventManagerBase.SetCallback(self, eventType, callback)

	if callable(callback):
	    self.widget.bind(eventType, callback)
	elif len(callback)>0:
	    self.BindFuncList(eventType, callback)
	else:
	    raise ValueError('First argument has to be a function or a list of\
functions')
	    
	return funcList


    def RemoveCallback(self, eventType, func):
	"""Delete function func from the list of callbacks for eventType"""

	EventManagerBase.RemoveCallback(self, eventType, func)

	if len(self.eventHandlers[eventType])==0:
	    self.widget.bind(eventType, self.DummyCallback)
	else:
	    self.BindFuncList(eventType, self.eventHandlers[eventType])
	return func


