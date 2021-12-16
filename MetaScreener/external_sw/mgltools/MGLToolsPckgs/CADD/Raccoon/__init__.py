#################################################################
# Vision - A Visual Programming Environment for Python
#
# Daniel Stoffler & Michel Sanner
# The Scripps Research Institute, La Jolla, CA
# sanner@scripps.edu, stoffler@scripps.edu
#
# Web: http://www.scripps.edu/~sanner/python/
#
# References:   
#    ViPEr, a Visual Programming Environment for Python 
#    In the Proceedings of The 10th International Python Conference 2002,
#    Virginia USA.
#    Michel F. Sanner, Daniel Stoffler, Arthur J. Olson
#    Won the award for the best paper at the Python conference
#    
#    Integrating biomolecular analysis and visual programming:
#    flexibility and interactivity in the design of bioinformatics tools 
#    In the proceedings of HICSS-36, Hawaii International conference
#    on system sciences, 2003, Hawaii
#    Daniel Stoffler, Sophie I. Coon, Ruth Huey, Arthur J. Olson,
#    and Michel F. Sanner
#
# revision: Guillaume Vareille
#
##################################################################
#
# $Header: /opt/cvs/CADD/Raccoon/__init__.py,v 1.2 2012/07/18 23:26:35 sanner Exp $
#
# $Id: __init__.py,v 1.2 2012/07/18 23:26:35 sanner Exp $
#

import time
import sys
import getopt
import os
import user
import warnings
import stat
from string import split

#sys.path.insert(0,'.')

from Support.version import __version__
from mglutil import __revision__
from mglutil.util.packageFilePath import setResourceFolder, getResourceFolder 

RACPATH = __path__[0]
ICONPATH = os.path.join(__path__[0], 'icons')
RESULTFILE = 'screening_report.log'

def createRoot():
    """ create a root and hide it
"""
    from Tkinter import Tk
    root = Tk()
    root.withdraw()
    return root


def createRaccoon(root=None, interactive=True):
    """
"""
    from CADD.Raccoon.raccoonGUI import RaccoonOpalGUI
    rac = RaccoonOpalGUI(root=root, debug=False, local_testing=0)
    return rac


def createSplash():
    """
"""
    iconsDir = os.path.join( __path__[0], 'icons')
    image_dir = os.path.join( iconsDir, 'images')

    # insert release date here
    from Support.version import __version__
    from mglutil import __revision__
    version = ' ' + __version__

    copyright = """(c) 2012 Molecular Simulation Laboratory, The Scripps Research Institute
    ALL RIGHTS RESERVED """
    authors = """Authors: Stefano Forli, Michel Sanner"""
    icon = os.path.join( iconsDir, 'raccoon.png')
    third_party = """"""

    text = 'Python executable   : '+sys.executable+'\n'
    #text += 'Vision script               : '+__file__+'\n'
    text += 'MGLTool packages  : '+'\n'
    
    from user import home
    updates_rc_dir = home + os.path.sep + ".mgltools" + os.sep + 'update'
    latest_tested_rc = updates_rc_dir + os.sep + 'latest_tested'
    latest_rc = updates_rc_dir + os.sep + 'latest' #may or may not be tested
    
    if os.path.exists(latest_tested_rc):
        p = open(latest_tested_rc).read()
        sys.path.insert(0, p)
        text += '    tested  : ' + p +'\n'
    
    if os.path.exists(latest_rc):
        p = open(latest_rc).read()
        sys.path.insert(0, p)
        text += '    nightly : ' + p +'\n'
    
    text += version + ': ' + 'ADD PATH HERE'
    path_data = text

    from mglutil.splashregister.splashscreen import SplashScreen
    from CADD.Raccoon.about import About
    about = About(image_dir=image_dir, third_party=third_party,
                  path_data=path_data,
                  title='Raccoon GUI', version='0.1',
                  revision='4', 
                  copyright=copyright, authors=authors, icon=icon)
    splash =  SplashScreen(about, noSplash=False)

    return splash, about


def runRaccoon(*argv, **kw):
    """
    The main function for running Raccoon
    """

    ##################################################################
    # Parse options
    ##################################################################

    if type(argv) is tuple:
        if len(argv) == 0:
            argv = None
        elif len(argv) == 1:
            argv = argv[0]
            if type(argv) is not list:
                argv = [argv]
        else:
            argv = list(argv)
    if kw.has_key("ownInterpreter"):
        ownInterpreter = kw["ownInterpreter"]
    else:
        if argv is None:
            argv = ['CADD/Raccoon/bin/raccoonLauncher.py']
            ownInterpreter = False
        elif argv[0].endswith('raccoonLauncher.py') is False:
            argv.insert(0,'CADD/Raccoon/bin/raccoonLauncher.py')
            ownInterpreter = False
        else:
            ownInterpreter = True

    help_msg = """usage: %s <options> <filenames>

    Files filenames ending in "net.py" will be laoded as networks in vision.
    Other files will be executed as Python scripts in which "ed" refers
    to the VisualProgrammingEnvironment instance.
    
            -h or --help : print this message
            -s or --noSplash : doesn't show the Vision splash screen (works only if registered)
            -t or --noTerminal : vision provides its own shell (under menu 'Edit') 
                           instead of the terminal
            --resourceFolder foldername  : stores resource file under .name (defaults to .mgltools)    
            -p or --ipython : create an ipython shell instead of a python shell        
            -r or --run  : run the networks on the command line
            -e or --runAndExit : run the networks and exit

            port values can be passed on the command line (but not to macros):
                             Network_net.py nodeName:portName:value

""" % sys.argv[0]

    try:
        optlist, args = getopt.getopt(argv[1:], 'hirestp', [
            'help', 'interactive', 'noTerminal', 'noSplash', 'resourceFolder=', 'run', 'runAndExit','ipython'] )
    except:
        print "Unknown option!"
        print help_msg
        return

    interactive = 1
    noSplash = False
    runNetwork = False
    once = False
    ipython = False
    for opt in optlist:
        if opt[0] in ('-h', '--help'):
            print help_msg
            return
        elif opt[0] in ('-i', '--interactive'):
            warnings.warn('-i (interactive) is default mode, use --noTerminal to disable it',
                          stacklevel=3)
        elif opt[0] in ('-t', '--noTerminal'):
            interactive = 0
        elif opt[0] in ('-s', '--noSplash',):
            noSplash = True
        elif opt[0] in ('--resourceFolder',):
            setResourceFolder(opt[1])
        elif opt[0] in ('-r', '--run'):
            runNetwork = True
        elif opt[0] in ('-e', '--runAndExit'):
            runNetwork = True
            once = True
        elif opt[0] in ('-p', '--ipython'):
            ipython = True

    from Support.path import path_text, release_path
    print 'Run Raccoon from ', __path__[0]
    
    if globals().has_key('rac') is False:
        root = createRoot()
        #root.withdraw()
        ##################################################################
        # Splash Screen
        ##################################################################
        if noSplash is False:
            splash, about = createSplash()
            lSplashVisibleTimeStart = time.clock()

        ##################################################################
        # Start Vision
        ##################################################################
        rac = createRaccoon(root, interactive)
        globals()['rac'] = rac

        ##################################################################
        # Source Resource File (if available)
        ##################################################################
        #if getResourceFolder() is None:
        #    print 'NO RESOURCE FOLDER'
        #else:
        #    print 'TODO source the raccon resource file'
        #    #rac.sourceFile(resourceFile='_visionrc')

        ##################################################################
        # Make sure splash is visible long enough before removing it
        ##################################################################
        if noSplash is False:
            lSplashVisibleTimeEnd = time.clock()
            while lSplashVisibleTimeEnd - lSplashVisibleTimeStart < 2:
                lSplashVisibleTimeEnd = time.clock()
            splash.finish()

        ##################################################################
        # Make vision visible 
        #(before the network loads, so the additional windows will load on top)
        ##################################################################
        if once is False:
            root.deiconify()

    else:
        rac = globals()['rac']
        root = rac.master
        root.master.master.deiconify()

    ##################################################################
    # Load network(s) if specified at startup
    ##################################################################
##     lResults = []
##     if len(args):
##         ed.root.update() # make sure the canvas is shown b4 loading any network
##         lArgIndex = 0
##         while lArgIndex < len(args):
##             if args[lArgIndex][-6:]=='net.py':
##                 ed.loadNetwork(args[lArgIndex], ins=kw.get('ins'))
##                 lNodePortValues = []
##                 lArgIndex += 1
##                 while lArgIndex < len(args) and args[lArgIndex][-3:]!='.py':
##                     lNodePortValues.append(args[lArgIndex])
##                     lArgIndex += 1
##                 ed.currentNetwork.setNodePortValues(lNodePortValues)
##                 if runNetwork:
##                     ed.softrunCurrentNet_cb()
##             elif args[lArgIndex][-3:]=='.py':
##                 execfile(netName)
##                 lArgIndex += 1
##             else:
##                 lArgIndex += 1

##         # lets obtain the asked outs values   
##         outs=kw.get('outs')
##         if outs is not None:
##             for lOut in outs:
##                 lOutFound = False
##                 for lNodes in ed.currentNetwork.nodes:
##                     if lNodes.name == lOut[0]:
##                         if lOutFound is True:
##                             warnings.warn("found several nodes %s"%lOut[0] )
##                         lOuputPort = lNodes.outputPortByName.get(lOut[1])
##                         if lOuputPort is None:
##                             warnings.warn("node %s doesn't have port %s"%(lOut[0],lOut[1]) )
##                         else:
##                            lResults.append(lOuputPort.data)
##                         lOutFound = True
##                 if lOutFound is False:
##                     warnings.warn("can't find node %s"%lOut[0] )

    if once is True:
        ed.root.quit()
        ed.root.destroy()
        globals().pop('ed')
        return lResults
    ##################################################################
    # Set the Python Shell
    ##################################################################
    elif ownInterpreter is True:
        if interactive:
            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

            mod = __import__('__main__')
            if ipython is True:
                try:
                    # create IPython shell
                    from IPython.Shell import _select_shell
                    sh = _select_shell([])(argv=[], user_ns=mod.__dict__)
                    sh.mainloop()
                except:
                    import code
                    try: # hack to really exit code.interact 
                        code.interact( 'Raccoon Interactive Shell', local=mod.__dict__)
                    except:
                        pass
            else:
                import code
                try: # hack to really exit code.interact 
                    code.interact( 'Raccoon Interactive Shell', local=mod.__dict__)
                except:
                    pass

        else:
            ed.master.mainloop()
    else:
        return lResults

#packageContainsVFCommands = 1

CRITICAL_DEPENDENCIES = ['NetworkEditor', 'mglutil', 'Support', 'Pmw', 'numpy']
NONCRITICAL_DEPENDENCIES = ['magick', 'PIL', 'opengltk', 'DejaVu', 'grail', 'MolKit', 'symserv','Volume', 'Pmv', 'matplotlib', 'pytz', 'AutoDockTools', 'IPython', 'pymedia']
