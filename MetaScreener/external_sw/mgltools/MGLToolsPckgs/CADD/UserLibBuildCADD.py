########################################################################
#########################################################################
# $Header: /opt/cvs/CADD/UserLibBuildCADD.py,v 1.4 2011/02/11 22:01:22 nadya Exp $
# $Id: UserLibBuildCADD.py,v 1.4 2011/02/11 22:01:22 nadya Exp $

import os
import shutil
import sys
import warnings
import stat
from inspect import isclass
from Vision.UserLibBuild import addDirToSysPath, userLibBuild

txtstr = """########################################################################
#
# Date: Feb 2008 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#    _fonts4cadd Resource File
#
########################################################################
# This file is optionnal and can be deleted,
# it is generated each time the fonts
# are modified via the Vision GUI
########################################################################

from mglutil.util.misc import ensureFontCase

self.setFont('Menus', (ensureFontCase('%s'),%s,'%s'))
self.setFont('LibTabs', (ensureFontCase('%s'),%s,'%s'))
self.setFont('Categories', (ensureFontCase('%s'),%s,'%s'))
self.setFont('LibNodes', (ensureFontCase('%s'),%s,'%s'))
self.setFont('NetTabs', (ensureFontCase('%s'),%s,'%s'))
self.setFont('Nodes', (ensureFontCase('%s'),%s,'%s'))
self.setFont('Root', (ensureFontCase('%s'),%s,'%s'))
"""

def ensureDefaultUserLibFileCADD():
    ##################################################################
    # verify or generate the default user lib file
    ##################################################################
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    userResourceFolder = getResourceFolderWithVersion()
    if userResourceFolder is None:
        return
    userCADDDir = userResourceFolder + os.sep + 'CADD' + os.sep
    userLibsDir = userCADDDir + 'UserLibs' + os.sep
    defaultLibDir = userLibsDir + 'MyDefaultLib' + os.sep
    defaultLibInit = defaultLibDir + '__init__.py'
    libTypesFile = defaultLibDir + 'libTypes.py'
    if os.path.isfile(defaultLibInit) is False:
        try:
            if os.path.isdir(userResourceFolder) is False:
                os.mkdir(userResourceFolder)
            if os.path.isdir(userCADDDir) is False:
                os.mkdir(userCADDDir)
            if os.path.isdir(userLibsDir) is False:
                os.mkdir(userLibsDir)
            if os.path.isdir(defaultLibDir) is False:
                os.mkdir(defaultLibDir)
            category1Dir = defaultLibDir + 'Input' + os.sep
            if os.path.isdir(category1Dir) is False:
                os.mkdir(category1Dir)
            category1Init = category1Dir + '__init__.py'
            if os.path.isfile(category1Init) is False:
                f = open(category1Init, "w")
                f.close()
            category2Dir = defaultLibDir + 'Output' + os.sep
            if os.path.isdir(category2Dir) is False:
                os.mkdir(category2Dir)
            category2Init = category2Dir + '__init__.py'
            if os.path.isfile(category2Init) is False:
                f = open(category2Init, "w")
                f.close()
            category3Dir = defaultLibDir + 'Macro' + os.sep
            if os.path.isdir(category3Dir) is False:
                os.mkdir(category3Dir)
            category3Init = category3Dir + '__init__.py'
            if os.path.isfile(category3Init) is False:
                f = open(category3Init, "w")
                f.close()
            category4Dir = defaultLibDir + 'Other' + os.sep
            if os.path.isdir(category4Dir) is False:
                os.mkdir(category4Dir)
            category4Init = category4Dir + '__init__.py'
            if os.path.isfile(category4Init) is False:
                f = open(category4Init, "w")
                f.close()
            f = open(defaultLibInit, "w")
            txt = """########################################################################
#
# Date: Jan 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#    Vision Library Loader
#
#########################################################################
#
# %s
# Vision will generate this file automatically if it can't find it
#

from os import sep, path
from Vision.VPE import NodeLibrary
from Vision.UserLibBuild import userLibBuild, addDirToSysPath, addTypes

dependents = {} # {'scipy':'0.6.0',} the numbers indicate the highest tested version of the needed packages
libraryColor = '#FF7700'

addDirToSysPath(path.dirname(__file__)+sep+'..')
fileSplit = __file__.split(sep)
if fileSplit[-1] == '__init__.pyc' or fileSplit[-1] == '__init__.py':
    libInstanceName = fileSplit[-2]
else:
    libInstanceName = path.splitext(fileSplit[-1])[0]
try:
    from Vision import ed
except:
    ed = None
if ed is not None and ed.libraries.has_key(libInstanceName):
    locals()[libInstanceName] = ed.libraries[libInstanceName]
else:
    locals()[libInstanceName] = NodeLibrary(libInstanceName, libraryColor, mode='readWrite')
success = userLibBuild(eval(libInstanceName), __file__, dependents=dependents)
if success is False:
    locals().pop(libInstanceName)
elif path.isfile(path.dirname(__file__)+sep+'libTypes.py'):
    addTypes(locals()[libInstanceName], libInstanceName + '.libTypes')

""" % defaultLibInit
            map( lambda x, f=f: f.write(x), txt )
            f.close()
            os.chmod(defaultLibInit, 0444) #make it read only

            f = open(libTypesFile, "w")
            txt = """########################################################################
#
# Date: Jan 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#    Vision Library Types
#
#########################################################################
#
# %s
# Vision will generate this file automatically if it can't find it
#

from NetworkEditor.datatypes import AnyArrayType

############################################################
# add new types to your library that the node ports can use. 
############################################################

#class ThingType(AnyArrayType):
#
#    from ThingPackage import Thing
#    def __init__(self, name='thing', color='#995699', shape='rect',
#                 klass=Thing):
#
#        AnyArrayType.__init__(self, name=name, color=color, shape=shape, 
#                              klass=klass)
#
## in NetworkEditor.datatypes, you should have a look at the class IntType

""" % libTypesFile
            map( lambda x, f=f: f.write(x), txt )
            f.close()

        except:
            txt = "Cannot write the init files %s and %s" %(defaultLibInit,libTypesFile)
            warnings.warn(txt)


def ensureCADDResourceFile():
    ##################################################################
    # verify or generate _caddrc file
    ##################################################################
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    
    caddrcDir = getResourceFolderWithVersion()
    if caddrcDir is None:
        return
    caddrcDir += os.sep + 'CADD'
    if os.path.isdir(caddrcDir) is False:
        try:
            os.mkdir(caddrcDir)
        except:
            txt = "can not create folder for _caddrc"
            warnings.warn(txt)
            return

    caddrcFile = caddrcDir + os.sep + '_caddrc'
    if os.path.isfile(caddrcFile) is False:
        try:
            from CADD import __path__ as lCADDPath
            shutil.copyfile(lCADDPath[0]+os.sep+'_caddrc', caddrcFile)
        except:
            txt = "can not create _caddrc"
            warnings.warn(txt)

    return caddrcFile

def ensureCADDFontsFile():
    ##################################################################
    # verify or generate _fonts4cadd file
    ##################################################################
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    
    caddrcDir = getResourceFolderWithVersion()
    if caddrcDir is None:
        return
    caddrcDir += os.sep + 'CADD'
    if os.path.isdir(caddrcDir) is False:
        try:
            os.mkdir(caddrcDir)
        except:
            txt = "can not create folder for _fonts4cadd"
            warnings.warn(txt)
            return

    fonts4CADDFile = caddrcDir + os.sep + '_fonts4cadd'
    try:
        f = open(fonts4CADDFile, "w")
        txt = txtstr % (
'helvetica', 10, 'normal',
'helvetica', 10, 'normal',
'helvetica', 10, 'normal',
'helvetica', 10, 'normal',
'helvetica', 10, 'normal',
'helvetica', 10, 'normal',
'helvetica', 10, 'normal'
)

        map( lambda x, f=f: f.write(x), txt )
        f.close()
    except:
        txt = "can not create _fonts4cadd"
        warnings.warn(txt)



def saveFonts4CADDFile(fontDict):
    ##################################################################
    # generate and overwrite _fonts4cadd file
    ##################################################################
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    
    caddrcDir = getResourceFolderWithVersion()
    if caddrcDir is None:
        return

    caddrcDir += os.sep + 'CADD'
    if os.path.isdir(caddrcDir) is False:
        return

    fonts4CADDFile = caddrcDir + os.sep + '_fonts4cadd'
    try:
        f = open(fonts4CADDFile, "w")
        txt = txtstr %(
fontDict['Menus'][0],fontDict['Menus'][1],fontDict['Menus'][2],
fontDict['LibTabs'][0],fontDict['LibTabs'][1],fontDict['LibTabs'][2],
fontDict['Categories'][0],fontDict['Categories'][1],fontDict['Categories'][2],
fontDict['LibNodes'][0],fontDict['LibNodes'][1],fontDict['LibNodes'][2],
fontDict['NetTabs'][0],fontDict['NetTabs'][1],fontDict['NetTabs'][2],
fontDict['Nodes'][0],fontDict['Nodes'][1],fontDict['Nodes'][2],
fontDict['Root'][0],fontDict['Root'][1],fontDict['Root'][2],
)

        map( lambda x, f=f: f.write(x), txt )
        f.close()
    except:
        txt = "can not create _fonts4cadd"
        warnings.warn(txt)


