############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 201
#
#############################################################################
"""
Module implementing the commands that are present when instanciating
an AppFramework class or AppFramework derived class.
   - loadModuleCommand
   - UndoCommand
   - RedoCommand
   - BrowseCommandsCommand
"""

# $Header: /opt/cvs/AppFramework/notOptionalCommands.py,v 1.7 2014/07/18 00:07:04 annao Exp $
#
# $Id: notOptionalCommands.py,v 1.7 2014/07/18 00:07:04 annao Exp $
#

## FIXME these should become part of the AppFramework rather than commands
##

import os, sys
from string import join

from mglutil.util.packageFilePath import findFilePath, findModulesInPackage
from AppFramework.AppCommands import AppCommand
from mglutil.events import Event

class NewUndoEvent(Event):
    pass

class AfterUndoEvent(Event):
    pass

class AfterRedoEvent(Event):
    pass


commandslist=[]
cmd_docslist={}
def findAllAppPackages():
    """Returns a list of package names found in sys.path"""
    packages = {}
    for p in ['.']+sys.path:
        flagline = []
        if not os.path.exists(p) or not os.path.isdir(p):
            continue
        files = os.listdir(p)
        for f in files:
            pdir = os.path.join(p, f)
            if not os.path.isdir(pdir):
                continue
            if os.path.exists( os.path.join( pdir, '__init__.py')) :
            
                fptr =open("%s/__init__.py" %pdir)
                Lines = fptr.readlines()
                flagline =filter(lambda x:x.startswith("packageContainsVFCommands"),Lines)
                if not flagline ==[]:
                    if not packages.has_key(f):
                        packages[f] = pdir
    return packages




class UndoCommand(AppCommand):
    """pops undo string from the stack and executes it in the AppFrameworks
    scope
    \nPackage : AppFramework
    \nModule : notOptionalCommands.py
    \nClass : UndoCommand
    \nCommand : Undo
    \nSynopsis:\n
        None <- Undo()
    """

    def validateUserPref(self, value):
        try:
            val = int(value)
            if val >-1:
                return 1
            else:
                return 0
        except:
            return 0


    def onAddCmdToApp(self):
        doc = """Number of commands that can be undone"""
        self.app().userpref.add( 'Number of Undo', 100,
                              validateFunc=self.validateUserPref,
                              doc=doc)


    def addUndoCall(self, cmdList, name):
        #print self.name, "addUndoCall for:", name
        # FIXME handle user pref
        self.cmdStack.append( (cmdList, name) )
        maxLen = self.app().userpref['Number of Undo']['value']
        if maxLen>0 and len(self.cmdStack)>maxLen:
            forget = self.cmdStack[:-maxLen]
            self.cmdStack = self.cmdStack[-maxLen:]

            for cmdList, name in forget:
                for cmd, args, kw in cmdList:
                    if hasattr(cmd, "handleForgetUndo"):
                        cmd.handleForgetUndo(*args, **kw)
        #the gui part of the application should register the following
        # event listener that will update the label if necessary
        event = NewUndoEvent(objects=self.cmdStack, command=self)
        self.app().eventHandler.dispatchEvent(event)

        
    def doit(self, **kw):
        """
        pop cmdList from stack and execute each cmd in cmdlList    
        """

        stack = self.cmdStack
        if stack:
            cmdList, name = stack.pop()
            ncmds = len(cmdList)
            self._cmdList = ([], name) # this list will gather undoCommands generated during the undo
            for i, (cmd, args, kw) in enumerate(cmdList):
                self.inUndo = ncmds-i-1
                if hasattr(cmd, 'name'):
                    name = cmd.name # this is a command
                else:
                    #a method or a function
                    if hasattr(cmd, "im_class"):
                        name = "%s.%s" % (cmd.im_class, cmd.__name__)
                    else:
                        name = cmd.__name__
                #msg = "Failed to run %s from %s"%(name, self.name)
                cmd( *args, **kw)
                #self.app().GUI.safeCall( cmd, msg, *args, **kw)
            self._cmdList = () # this list will gather undoCommands generated during the undo
            #self.inUndo = True
            #for cmd, args, kw in cmdList:
            #    cmd( *args, **kw)
            #self.inUndo = False
            self.inUndo = -1
        else:
            self.app().warningMsg('ERROR: Undo called for %s when undo stack is empty'%\
                               self.name)
        event = AfterUndoEvent(objects=self.cmdStack, command=self)
        self.app().eventHandler.dispatchEvent(event)

    def __init__(self):
        AppCommand.__init__(self)
        # cmdStack is a list of tuples providing 1-a list of commands to execute and 2 a name for this operation
        # the list of commands is in the following format [ (cmd, *args, **kw) ]
        self.cmdStack = []
        self.inUndo = -1 # will be 0 or a positive integer  while we are executing command(s) to undo last operation.
        self._cmdList = () # this tuple will contain a list that will collect negation of commands during a loop over commands
                           # corresponding to an Undo (or Redo in subclassed command)

    def checkArguments(self, **kw):
        """None<---NEWundo()
        """
        kw['topCommand'] = 0
        return (), kw


    def resetCmdStack(self):
        #remove all items from self.cmdStack
        if len(self.cmdStack):
            del(self.cmdStack)
            self.cmdStack = []
            event = AfterUndoEvent(objects=self.cmdStack, command=self)
            self.app().eventHandler.dispatchEvent(event)


    def cleanCmdStack(self, molecule):
        # when a molecule is deleted in an not undoable way we need to
        # remove references to this molecule from the undo/redo cmd stack

        # go over the stored commands (commmand.cmdStack) and remove the ones that 
        # contain given molecule in their argument tuples.
        removedEntries = [] # will contain indices of entries that need to be
                            # removed from command.cmdStack
        #print "cleaning up %s  cmdStack" % command.name
        from MolKit.tree import TreeNode, TreeNodeSet

        # loop over undo/redo comand stack
        for i, cmdEntry in enumerate(self.cmdStack):
            cmdList = cmdEntry[0] # get a handle to (cmd *args, **kw)
            remove = False
            # loop over commands in this undo block
            for j, cmd in enumerate(cmdList):
                if remove: break
                for arg in cmd[1]: # FIXME this loop might not be necessary
                                   # if the only place for molecular fragments
                                   # is the first argument

                    #if the arg is a molecular fragment
                    if isinstance(arg, TreeNode):
                        if arg.top==molecule:
                            removedEntries.append(i)
                            remove = True
                            break
                        
                    elif isinstance(arg, TreeNodeSet):
                        deleted = molecule.findType(arg.elementType)
                        new = arg - deleted
                        if len(new)==0:
                            removedEntries.append(i)
                            remove = True
                            break
                        #else:
                            # replace arg that contains reference to this molecule and some other
                            # molecule(s) by new.  
                            #cmdList[j] = (cmdList[j][0], (new,), cmdList[j][2])
                            # FIXME: this is not sufficient , we need to find a way to
                            # check all kw of the command to see if they contain vectors of colors, etc
                            # for this molecule.
                            #for now we remove all cmdStack entries containig reference to this molecule.
                        elif new == arg:
                            remove = False
                            break
                        else:
                            removedEntries.append(i)
                            remove = True
                            break
                    else: #not  TreNodeSet , not TreNode
                        #FIX ME (ex: AddBondsCommand takes a list of atom pairs ....
                        # maybe there are more cases like this one)
                        # remove it - for now
                        removedEntries.append(i)
                        remove = True
                        break
        # remove selected entries
        n = 0
        for i in removedEntries:
            self.cmdStack.pop(i-n)
            n = n+1
        event = AfterUndoEvent(objects=self.cmdStack, command=self)
        self.app().eventHandler.dispatchEvent(event)


class  RedoCommand(UndoCommand):
    """pops redo cmdList from the stack and executes it in the AppFrameworks
    scope
    \nPackage : AppFramework
    \nModule : notOptionalCommands.py
    \nClass : RedoCommand
    \nCommand : Undo
    \nSynopsis:\n
        None <- Undo()
    """
    pass


class BrowseCommandsCommand(AppCommand):
    """Command to load dynamically either modules or individual commands
    in the Application.
    \nPackage : AppFramework
    \nModule : notOptionalCommands.py
    \nClass : BrowseCommandsCommand
    \nCommand : browseCommands
    \nSynopsis:\n
        None <-- browseCommands(module, commands=None, package=None, **kw)
    \nRequired Arguements:\n
        module --- name of the module(eg:colorCommands)
    \nOptional Arguements:\n
        commnads --- one list of commands to load
        \npackage --- name of the package to which module belongs(eg:Pmv,Vision)
    """
    def __init__(self):
        AppCommand.__init__(self)
        self.allPack = {}
        self.packMod = {}
        self.allPackFlag = False
        self.txtGUI = ""


    def doit(self, module, commands=None, package=None, removable=False, gui=False):
#        if removable:
#            self.app().removableCommands.settings[module] = [commands, package]
#            self.app().removableCommands.saveAllSettings()
        # If the package is not specified the default is the first library

        #global commandslist,cmd_docslist
        #import pdb
        #pdb.set_trace()
        if package is None: package = self.app().libraries[0]

        importName = package + '.' + module
        try:
            # try to execute import Pmv.colorCommands
            mod = __import__(importName, globals(), locals(),
                            [module])
        except:
            if self.cmdForms.has_key('loadCmds') and \
                self.cmdForms['loadCmds'].f.winfo_toplevel().wm_state() == \
                                                                       'normal':
                   self.app().errorMsg(sys.exc_info(),
                                       "ERROR: Could not load module %s"%module,
                                       obj=module )
            elif self.app().loadModule.cmdForms.has_key('loadModule') and \
                self.app().loadModule.cmdForms['loadModule'].f.winfo_toplevel().wm_state() == \
                                                                       'normal':
                   self.app().errorMsg(sys.exc_info(),
                                       "ERROR: Could not load module %s"%module,
                                       obj=module)
            else:
                self.app().errorMsg(sys.exc_info(),
                                    "ERROR: Could not load module %s"%module,
                                    obj=module)
            #import traceback
            #traceback.print_exc()

        if commands is None:
            # no particular commmand is asked for, so we try
            # to run the initModule
            if hasattr(mod,"initModule"):
                mod.initModule(self.app(), gui=gui)
            elif hasattr(mod, 'commandList'):
                for d in mod.commandList:
                    cmd = d['cmd'].__class__()
                    self.app().addCommand( cmd, d['name'], None)
            elif hasattr(mod, 'commandClassFromName'):
                for name, values in mod.commandClassFromName.items():
                    cmd = values[0]()
                    self.app().addCommand( cmd, name, None)
            else :
                raise RuntimeError, "cannot load module %s, missing init"%importName

        else:  # a single com,mand or a list of commands was given
            if isinstance(commands, str):
                commands = [commands,]

            elif hasattr(mod, 'commandList'):
                for cmdName in commands:
                    found = False
                    for d in mod.commandList:
                        if d['name']==cmdName:
                            cmd = d['cmd'].__class__()
                            self.app().addCommand( cmd, d['name'], d['gui'])
                            found = True
                            break
                    if not Found:
                        raise RuntimeError, 'ERROR: cmd %s not found in %s'%(cmdName, importName)
                        
            elif hasattr(mod, 'commandClassFromName'):
                for cmdName in commands:
                    values = mod.commandClassFromName.get(cmdName, None)
                    if values:
                        cmd = values[0]()
                        # FIXME gui are instances, that measn that 2 PMV would share
                        # these instances :(. Lazy loading fixes this since the GUI is
                        # created independently
                        gui = values[1]
                        self.app().addCommand( cmd, cmdName, gui)
                    else:
                        raise RuntimeError, 'ERROR: cmd %s not found in %s'%(cmdName, importName)
            else :
                raise RuntimeError, "cannot load module %s, missing init"%importName


    def checkArguments(self, module, commands=None, package=None, **kw):
        """None<---browseCommands(module, commands=None, package=None, **kw)
        \nmodule --- name of the module(eg:colorCommands)
        \ncommnads --- one list of commands to load
        \npackage --- name of the package to which module belongs(eg:Pmv,Vision)
        """
        kw['commands'] = commands
        kw['package'] = package
        return (module,), kw 
    
    # the following code should go to the GUI part of the Command
##     def buildFormDescr(self, formName):
##         import Tkinter, Pmw
##         from mglutil.gui.InputForm.Tk.gui import InputFormDescr
##         from mglutil.gui.BasicWidgets.Tk.customizedWidgets import kbScrolledListBox
##         if not formName == 'loadCmds': return
##         idf = InputFormDescr(title='Load Modules and Commands')
##         pname = self.app().libraries
##         #when Pvv.startpvvCommnads is loaded some how Volume.Pvv is considered
##         #as seperate package and is added to packages list in the widget
##         #To avoid this packages having '.' are removed
##         for p in pname:
##             if '.' in p:
##                 ind = pname.index(p)
##                 del pname[ind]
        
##         idf.append({'name':'packList',
##                     'widgetType':kbScrolledListBox,
##                     'wcfg':{'items':pname,
##                             #'defaultValue':pname[0],
##                             'listbox_exportselection':0,
##                             'labelpos':'nw',
##                             'label_text':'Select a package:',
##                             #'dblclickcommand':self.loadMod_cb,
##                             'selectioncommand':self.displayMod_cb
##                             },
##                     'gridcfg':{'sticky':'wesn'}})
        
        
##         idf.append({'name':'modList',
##                     'widgetType':kbScrolledListBox,
##                     'wcfg':{'items':[],
##                             'listbox_exportselection':0,
##                             'labelpos':'nw',
##                             'label_text':'Select a module:',
##                             #'dblclickcommand':self.loadMod_cb,
##                             'selectioncommand':self.displayCmds_cb,
##                             },
##                     'gridcfg':{'sticky':'wesn', 'row':-1}})

##         idf.append({'name':'cmdList',
##                     'widgetType':kbScrolledListBox,
##                     'wcfg':{'items':[],
##                             'listbox_exportselection':0,
##                             'listbox_selectmode':'extended',
##                             'labelpos':'nw',
##                             'label_text':'Available commands:',
##                             #'dblclickcommand':self.loadCmd_cb,
##                             'selectioncommand':self.displayCmd_cb,
##                             },
##                     'gridcfg':{'sticky':'wesn', 'row':-1}})

## #        idf.append({'name':'docbutton',
## #                    'widgetType':Tkinter.Checkbutton,
## #                    #'parent':'DOCGROUP',
## #                    'defaultValue':0,
## #                    'wcfg':{'text':'Show documentation',
## #                               'onvalue':1,
## #                               'offvalue':0,
## #                               'command':self.showdoc_cb,
## #                               'variable':Tkinter.IntVar()},
## #                        'gridcfg':{'sticky':'nw','columnspan':3}})
                    
##         idf.append({'name':'DOCGROUP',
##                         'widgetType':Pmw.Group,
##                         'container':{'DOCGROUP':"w.interior()"},
##                         'collapsedsize':0,
##                         'wcfg':{'tag_text':'Description'},
##                         'gridcfg':{'sticky':'wnse', 'columnspan':3}})

##         idf.append({'name':'doclist',
##                     'widgetType':kbScrolledListBox,
##                     'parent':'DOCGROUP',
##                     'wcfg':{'items':[],
##                             'listbox_exportselection':0,
##                             'listbox_selectmode':'extended',
##                             },
##                     'gridcfg':{'sticky':'wesn', 'columnspan':3}})
        
##         idf.append({'name':'allPacks',
##                     'widgetType':Tkinter.Button,
##                     'wcfg':{'text':'Show all packages',
##                             'command':self.allPacks_cb},
##                     'gridcfg':{'sticky':'ew'}})

##         idf.append({'name':'loadMod',
##                     'widgetType':Tkinter.Button,
##                     'wcfg':{'text':'Load selected module',
##                             'command':self.loadMod_cb},
##                     'gridcfg':{'sticky':'ew', 'row':-1}})

## #        idf.append({'name':'loadCmd',
## #                    'widgetType':Tkinter.Button,
## #                    'wcfg':{'text':'Load Command',
## #                            'command':self.loadCmd_cb},
## #                    'gridcfg':{'sticky':'ew', 'row':-1}})

##         idf.append({'name':'dismiss',
##                     'widgetType':Tkinter.Button,
##                     'wcfg':{'text':'Dismiss',
##                             'command':self.dismiss_cb},
##                     'gridcfg':{'sticky':'ew', 'row':-1}})

## #        idf.append({'name':'dismiss',
## #                    'widgetType':Tkinter.Button,
## #                    'wcfg':{'text':'DISMISS',
## #                            'command':self.dismiss_cb,
## #                           },
## #                    'gridcfg':{'sticky':Tkinter.E+Tkinter.W,'columnspan':3}})

##         return idf

##     def guiCallback(self):
##         self.app().GUI.ROOT.config(cursor='watch')
##         self.app().GUI.ROOT.update()
##         if self.allPack == {}:
##             self.allPack = findAllVFPackages()
##         val = self.showForm('loadCmds', force=1,modal=0,blocking=0)
##         ebn = self.cmdForms['loadCmds'].descr.entryByName
## #        docb=ebn['docbutton']['widget']
## #        var=ebn['docbutton']['wcfg']['variable'].get()
## #        if var==0:
## #            dg=ebn['DOCGROUP']['widget']
## #            dg.collapse()
##         self.app().GUI.ROOT.config(cursor='')
        
##     def dismiss_cb(self, event=None):
##         self.cmdForms['loadCmds'].withdraw()
        
##     def allPacks_cb(self, event=None):
##         ebn = self.cmdForms['loadCmds'].descr.entryByName
##         packW = ebn['packList']['widget']
##         if not self.allPackFlag:
##             packName = self.allPack.keys()
##             packW.setlist(packName)
##             ebn['allPacks']['widget'].configure(text='Show default packages')
##             self.allPackFlag = True
##         else:
##             packName = self.app().libraries
##             packW.setlist(packName)
##             ebn['allPacks']['widget'].configure(text='Show all packages')
##             self.allPackFlag = False
            
##         ebn['modList']['widget'].clear()
##         ebn['cmdList']['widget'].clear()


##     def displayMod_cb(self, event=None):
##         #print "displayMod_cb"

## #        c = self.cmdForms['loadCmds'].mf.cget('cursor')
        
## #        self.cmdForms['loadCmds'].mf.configure(cursor='watch')
## #        self.cmdForms['loadCmds'].mf.update_idletasks()
##         ebn = self.cmdForms['loadCmds'].descr.entryByName
## #        docb=ebn['docbutton']['widget']
## #        var=ebn['docbutton']['wcfg']['variable'].get()
## #        dg = ebn['DOCGROUP']['widget']
## #        dg.collapse()
##         packW = ebn['packList']['widget']
##         packs = packW.getcurselection()
##         if len(packs) == 0:
##             return
##         packName = packs[0]
##         if not self.packMod.has_key(packName):
##             package = self.allPack[packName]
##             self.packMod[packName] = findModulesInPackage(package,"^def initModule",fileNameFilters=['Command'])
##         self.currentPack = packName
##         modNames = []
##         for key, value in self.packMod[packName].items():
##             pathPack = key.split(os.path.sep)
##             if pathPack[-1] == packName:
##                 newModName = map(lambda x: x[:-3], value)
##                 #for mname in newModName:
##                    #if "Command" not in mname :
##                        #ind = newModName.index(mname)
##                        #del  newModName[ind]
##                 modNames = modNames+newModName       
##             else:
##                 pIndex = pathPack.index(packName)
##                 prefix = join(pathPack[pIndex+1:], '.')
##                 newModName = map(lambda x: "%s.%s"%(prefix, x[:-3]), value)
##                 #for mname in newModName:
##                     #if "Command" not in mname :
##                         #ind = newModName.index(mname)
##                         #del  newModName[ind]
##                 modNames = modNames+newModName       
##         modNames.sort()
##         modW = ebn['modList']['widget']
##         modW.setlist(modNames)
##         # and clear contents in self.libraryGUI
##         cmdW = ebn['cmdList']['widget']
##         cmdW.clear()
##         m = __import__(packName, globals(), locals(),[])
##         d = []
##         docstring=m.__doc__
##         #d.append(m.__doc__)
##         docw = ebn['doclist']['widget']
##         docw.clear()
##         #formatting documentation. 
##         if docstring!=None :
##             if '\n' in docstring:
##                 x = docstring.split("\n")
##                 for i in x:
##                     if i !='':
##                         d.append(i)
##                     if len(d)>8:
##                         docw.configure(listbox_height=8)        
##                     else:
##                         docw.configure(listbox_height=len(d))
##             else:
##                 x = docstring.split(" ")
##                 #formatting documenation
##                 if len(x)>10:
##                     docw.configure(listbox_height=len(x)/10)
##                 else:
##                     docw.configure(listbox_height=1)
            
        
        
##         docw.setlist(d)
        
##  #       self.cmdForms['loadCmds'].mf.configure(cursor=c)
##         #when show documentation on after selcting a package
##         #dg is expanded to show documenttation
##         #if var==1 and docw.size()>0:
##         ##if docw.size()>0:
##         ##    dg.expand()


##     def displayCmds_cb(self, event=None):
##         #print "displayCmds_cb"

##         global cmd_docslist
##         self.cmdForms['loadCmds'].mf.update_idletasks()

##         ebn = self.cmdForms['loadCmds'].descr.entryByName
##         dg = ebn['DOCGROUP']['widget'] 
##         dg.collapse()
##         cmdW = ebn['cmdList']['widget']
##         cmdW.clear()

## #        docb=ebn['docbutton']['widget']
## #        var=ebn['docbutton']['wcfg']['variable'].get()
##         modName = ebn['modList']['widget'].getcurselection()
##         if modName == (0 or ()): return
##         else: 
##             modName = modName[0]
##         importName = self.currentPack + '.' + modName
##         try:
##             m = __import__(importName, globals(), locals(),['commandList'])
##         except:
##             return

##         if not hasattr(m, 'commandList'):
##             return
##         cmdNames = map(lambda x: x['name'], m.commandList)
##         cmdNames.sort()
##         if modName:
##             self.var=1
##             d =[]
##             docstring =m.__doc__

##             docw = ebn['doclist']['widget']
##             docw.clear()
##             if docstring!=None :
##                     if '\n' in docstring:
##                         x = docstring.split("\n")
##                         for i in x:
##                             if i !='':
##                                 d.append(i)
##                         #formatting documenation
##                         if len(d)>8:
##                             docw.configure(listbox_height=8)        
##                         else:
##                             docw.configure(listbox_height=len(d))
##                     else:
##                          d.append(docstring)
##                          x = docstring.split(" ")
##                          #formatting documenation
##                          if len(x)>10:
##                             docw.configure(listbox_height=len(x)/10)
##                          else:
##                             docw.configure(listbox_height=1)
                    
##             docw.setlist(d)
##         CmdName=ebn['cmdList']['widget'].getcurselection()
##         cmdW.setlist(cmdNames)

##         #when show documentation is on after selcting a module or a command
##         #dg is expanded to show documenttation 
##         #if var==1 and docw.size()>0:
##         if docw.size()>0:
##              dg.expand()


##     def displayCmd_cb(self, event=None):
##         #print "displayCmd_cb"
        
##         global cmd_docslist
##         self.cmdForms['loadCmds'].mf.update_idletasks()

##         ebn = self.cmdForms['loadCmds'].descr.entryByName
##         dg = ebn['DOCGROUP']['widget'] 
##         dg.collapse()
## #        docb=ebn['docbutton']['widget']
## #        var=ebn['docbutton']['wcfg']['variable'].get()
##         modName = ebn['modList']['widget'].getcurselection()
##         if modName == (0 or ()): return
##         else: 
##             modName = modName[0]
##         importName = self.currentPack + '.' + modName
##         try:
##             m = __import__(importName, globals(), locals(),['commandList'])
##         except:
##             self.warningMsg("ERROR: Cannot find commands for %s"%modName)
##             return

##         if not hasattr(m, 'commandList'):
##             return
##         cmdNames = map(lambda x: x['name'], m.commandList)
##         cmdNames.sort()
##         if modName:
##             self.var=1
##             d =[]
##             docstring =m.__doc__
##             import string
##             docw = ebn['doclist']['widget']
##             docw.clear()
##             if docstring!=None :
##                     if '\n' in docstring:
##                         x = docstring.split("\n")
##                         for i in x:
##                             if i !='':
##                                 d.append(i)
##                         #formatting documenation
##                         if len(d)>8:
##                             docw.configure(listbox_height=8)        
##                         else:
##                             docw.configure(listbox_height=len(d))
##                     else:
##                          d.append(docstring)
##                          x = docstring.split(" ")
##                          #formatting documenation
##                          if len(x)>10:
##                             docw.configure(listbox_height=len(x)/10)
##                          else:
##                             docw.configure(listbox_height=1)
                    
##             docw.setlist(d)
##         cmdW = ebn['cmdList']['widget']
##         CmdName=ebn['cmdList']['widget'].getcurselection()
##         cmdW.setlist(cmdNames)
##         if len(CmdName)!=0:
##             for i in m.commandList:
##                 if i['name']==CmdName[0]:
##                     c = i['cmd']
##             if CmdName[0] in cmdNames:
##                 ind= cmdNames.index(CmdName[0])
##                 cmdW.selection_clear()
##                 cmdW.selection_set(ind)
##                 d =[]
##                 docstring=c.__doc__
##                 docw = ebn['doclist']['widget']
##                 docw.clear()
##                 if CmdName[0] not in cmd_docslist.keys():
##                     cmd_docslist[CmdName[0]]=d
##                 import string
##                 if docstring!=None :
##                     if '\n' in docstring:
##                         x = docstring.split("\n")
##                         for i in x:
##                             if i !='':
##                                 d.append(i)
##                         if len(d)>8:
##                             docw.configure(listbox_height=8)
##                         else:
##                             docw.configure(listbox_height=len(d))
##                     else:
##                         d.append(docstring)
##                         x = docstring.split(" ")
##                         if len(x)>10:
##                             docw.configure(listbox_height=len(x)/10)
##                         else:
##                             docw.configure(listbox_height=1)
                               
##                 docw.setlist(d)    
##         #when show documentation is on after selcting a module or a command
##         #dg is expanded to show documenttation 
##         #if var==1 and docw.size()>0:
##         if docw.size()>0:
##              dg.expand()


##     def loadMod_cb(self, event=None):
##         ebn = self.cmdForms['loadCmds'].descr.entryByName
##         selMod = ebn['modList']['widget'].getcurselection()
##         if len(selMod)==0: return
##         else:
##             self.txtGUI = ""
##             apply(self.doitWrapper, ( selMod[0],),
##                   {'commands':None, 'package':self.currentPack, 'removable':True})
##             self.dismiss_cb(None)
##             if self.txtGUI:
##                 self.txtGUI = "\n Access this command via:\n"+self.txtGUI
##             import tkMessageBox
##             tkMessageBox.showinfo("Load Module", selMod[0]+" loaded successfully!\n"+self.txtGUI)



class loadModuleCommand(AppCommand):
    """Command to load dynamically modules to the App. import the file called name.py and execute the function initModule defined in that file Raises a ValueError exception if initModule is not defined
    \nPackage : AppFramework
    \nModule : notOptionalCommands.py
    \nClass : loadModuleCommand
    \nCommand : loadModule
    \nSynopsis:\n
        None<--loadModule(filename, package=None, **kw)
    \nRequired Arguements:\n
        filename --- name of the module
    \nOptional Arguments:\n   
        package --- name of the package to which filename belongs
    """

    active = 0
    
    def doit(self, filename, package):
        # This is NOT called because we call browseCommand()"
        if package is None:
            _package = filename
        else:
            _package = "%s.%s"%(package, filename)
        try:
            mod = __import__( _package, globals(), locals(), ['initModule'])
            if hasattr(mod, 'initModule') or not callable(mod.initModule):
                mod.initModule(self.app())
            else:
                self.app().errorMsg(sys.exc_info(), '%s:Module %s does not have initModule function'%(self.name, filename))    
        except:
            self.app().errorMsg(sys.exc_info(), '%s:Module %s could not be imported'%(self.name, _package))
        
            

    def checkArguments(self, filename, package=None, **kw):
        """None<---loadModule(filename, package=None, **kw)
        \nRequired Arguements:\n
            filename --- name of the module
        \nOptional Arguements:\n   
            package --- name of the package to which filename belongs
        """
        if package==None:
            package=self.app().libraries[0]
        if not kw.has_key('redraw'):
            kw['redraw'] = 0
        kw['package'] = package
        return (filename,), kw




    def loadModules(self, package, library=None):
        modNames = []
        doc = []
        self.filenames={}
        self.allPack={}
        self.allPack=findAllVFPackages()
        if package is None: return [], []
        if not self.filenames.has_key(package):
            pack=self.allPack[package]
            #finding modules in a package
            self.filenames[pack] =findModulesInPackage(pack,"^def initModule",fileNameFilters=['Command'])
        # dictionary of files keys=widget, values = filename
        for key, value in self.filenames[pack].items():
            pathPack = key.split(os.path.sep)
            if pathPack[-1] == package:
                newModName = map(lambda x: x[:-3], value)
                #for mname in newModName:
                   #if not modulename has Command in it delete from the
                   #modules list  
                   #if "Command" not in mname :
                       #ind = newModName.index(mname)
                       #del  newModName[ind]
                   #if "Command"  in mname :
                if hasattr(newModName,"__doc__"):
                    doc.append(newModName.__doc__)
                else:
                    doc.append(None)
                modNames = modNames + newModName
                
            else:
                pIndex = pathPack.index(package)
                prefix = join(pathPack[pIndex+1:], '.')
                newModName = map(lambda x: "%s.%s"%(prefix, x[:-3]), value)
                #for mname in newModName:
                   #if not modulename has Command in it delete from the
                   #modules list
                   #if "Command" not in mname :
                       #ind = newModName.index(mname)
                       #del  newModName[ind]
                if hasattr(newModName,"__doc__"):
                    doc.append(newModName.__doc__)
                else:
                    doc.append(None)      
                modNames = modNames + newModName
            modNames.sort()
            return modNames, doc     


    # The following code should go to the GUI part of the command    
    ## def loadModule_cb(self, event=None):
        
    ##     ebn = self.cmdForms['loadModule'].descr.entryByName
    ##     moduleName = ebn['Module List']['widget'].get()
    ##     package = ebn['package']['widget'].get()
    ##     if moduleName:
    ##         self.app().browseCommands(moduleName[0], package=package, redraw=0)        


    ## def package_cb(self, event=None):
    ##     ebn = self.cmdForms['loadModule'].descr.entryByName
    ##     pack = ebn['package']['widget'].get()
    ##     names, docs = self.loadModules(pack)
    ##     w = ebn['Module List']['widget']
    ##     w.clear()
    ##     for n,d in map(None, names, docs):
    ##         w.insert('end', n, d)

    ## def buildFormDescr(self, formName):
    ##     """create the cascade menu for selecting modules to be loaded"""
    ##     if not formName == 'loadModule':return
    ##     import Tkinter, Pmw
    ##     from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
        
    ##     ifd = InputFormDescr(title='Load command Modules')
    ##     names, docs = self.loadModules(self.app().libraries[0])
    ##     entries = map(lambda x: (x, None), names)
    ##     pname=self.app().libraries
    ##     for p in pname:
    ##         if '.' in p:
    ##             ind = pname.index(p)
    ##             del pname[ind]
    ##     ifd.append({
    ##         'name':'package',
    ##         'widgetType': Pmw.ComboBox,
    ##         'defaultValue': pname[0],
    ##         'wcfg':{ 'labelpos':'nw', 'label_text':'Package:',
    ##                  'selectioncommand': self.package_cb,
    ##                  'scrolledlist_items':pname
    ##                  },
    ##         'gridcfg':{'sticky':'ew', 'padx':2, 'pady':1}
    ##         })
        
    ##     ifd.append({'name': 'Module List',
    ##                 'widgetType':ListChooser,
    ##                 'wcfg':{
    ##                     'title':'Choose a module',
    ##                     'entries': entries,
    ##                     'lbwcfg':{'width':27,'height':10},
    ##                     'command':self.loadModule_cb,
    ##                     'commandEvent':"<Double-Button-1>"
    ##                     },
    ##                 'gridcfg':{'sticky':Tkinter.E+Tkinter.W}
    ##                 })

    ##     ifd.append({'name': 'Load Module',
    ##                 'widgetType':Tkinter.Button,
    ##                 'wcfg':{'text':'Load Module',
    ##                         'command': self.loadModule_cb,
    ##                         'bd':6},
    ##                 'gridcfg':{'sticky':Tkinter.E+Tkinter.W},
    ##                 })

    ##     ifd.append({'widgetType':Tkinter.Button,
    ##                 'wcfg':{'text':'Dismiss',
    ##                         'command': self.Dismiss_cb},
    ##                 'gridcfg':{'sticky':Tkinter.E+Tkinter.W}})
    ##     return ifd

    ## def Dismiss_cb(self):
    ##     self.cmdForms['loadModule'].withdraw()
    ##     self.active = 0
        

    ## def guiCallback(self, event=None):
    ##     if self.active: return
    ##     self.active = 1
    ##     form = self.showForm('loadModule', force=1,modal=0,blocking=0)
    ##     form.root.protocol('WM_DELETE_WINDOW',self.Dismiss_cb)
