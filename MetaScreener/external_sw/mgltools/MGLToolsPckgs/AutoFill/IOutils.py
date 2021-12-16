# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 09:04:10 2013

@author: Ludovic Autin
"""
import numpy
import AutoFill

def getValueToXMLNode(vtype,node,attrname):
#        print "getValueToXMLNode ",attrname
    value = node.getAttribute(attrname)
#        print "value " , value
    value = str(value)
    if not len(value):
        return None
    if vtype not in ["liste","filename","string"] :
        value=eval(value)
    else :
        value=str(value)
    return value
           
def setValueToXMLNode(value,node,attrname):
    if value is None:
        print (attrname, " is None !")
        return
    if attrname == "color" :
        if type(value) != list and type(value) != tuple :
            if AutoFill.helper is not None : 
                value=AutoFill.helper.getMaterialProperty(value,["color"])[0]
            else :
                value = [1.,0.,0.]
    if type (value) == numpy.ndarray :
        value = value.tolist()
    elif type(value) == list or type(value) == tuple:
        for i,v in enumerate(value) :
            if type(v) == numpy.ndarray :
                value[i] = v.tolist()
            elif type(v) == list  or type(v) == tuple:
                for j,va in enumerate(v) :
                    if type(va) == numpy.ndarray :
                        v[j] = va.tolist()                        
    node.setAttribute(attrname,str(value))
 
def setValueToPythonStr(value,attrname):  
    if value is None:
        print (attrname, " is None !")
        return 
    if attrname == "color" :
        if type(value) != list and type(value) != tuple :
            if AutoFill.helper is not None : 
                value=AutoFill.helper.getMaterialProperty(value,["color"])[0]
            else :
                value = [1.,0.,0.]
    if type (value) == numpy.ndarray :
        value = value.tolist()
    elif type(value) == list :
        for i,v in enumerate(value) :
            if type(v) == numpy.ndarray :
                value[i] = v.tolist()
            elif type(v) == list :
                for j,va in enumerate(v) :
                    if type(va) == numpy.ndarray :
                        v[j] = va.tolist()                        
#        print ("setValueToXMLNode ",attrname,value,str(value))  
    if type (value) == str:
        return "%s = '%s'" % (attrname,str(value))
    else :
        return "%s = %s" % (attrname,str(value))  
     