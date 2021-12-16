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
# $Header: /opt/cvs/DejaVu2/Tk/__init__.py,v 1.1.1.1 2014/06/19 19:41:03 sanner Exp $
#
# $Id: __init__.py,v 1.1.1.1 2014/06/19 19:41:03 sanner Exp $
#

from Tkinter import _default_root, Tk

def loadTogl(master):
    # simulate the setting of TCLLIPATH

    import sys, os
    from os import path
    # Togl is expected to be 

    # build path to directory containing Togl
    from opengltk.OpenGL import Tk
    ToglPath = path.dirname(path.abspath(Tk.__file__))
    # get TCL interpreter auto_path variable
    tclpath = master.tk.globalgetvar('auto_path')

    # ToglPath not already in there, add it
    from string import split
    if ToglPath not in tclpath:
        tclpath = (ToglPath,) + tclpath
        master.tk.globalsetvar('auto_path', tclpath )
    # load Togl extension into TCL interpreter

    #if os.name == 'nt':
    #    toglVersion = master.tk.call('package', 'require', 'Togl','1.7')  
    #else:
    #    toglVersion = master.tk.call('package', 'require', 'Togl','2.1')
    toglVersion = master.tk.call('package', 'require', 'Togl','2.1')

    return toglVersion


