#############################################################################
#
# Author: Ruth HUEY, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2008
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/AutoDockTools/autoflex4Commands.py,v 1.1 2008/06/04 15:37:20 rhuey Exp $ 
#
# $Id: autoflex4Commands.py,v 1.1 2008/06/04 15:37:20 rhuey Exp $
#
#
#
#
#
"""
This Module facilitates producing a formatted flexible residue file for AutoDock. The steps in this process are:

    * Set the macromolecule: 

        o Read a PDBQT Macromolecule 

        o Choose Macromol...

    * Select which residues are to be flexible in macromolecule using Pmv selection tools:

        o ICOM Select 

        o SelectFromString

        o Select Spherical Region

    * Set which torsions in the sidechains of those residues are to be flexible interactively

    * The results of the previous steps are written to two files: 

        o one containing the sidechains of the flexible residues with special keywords

        o a second containing the rigid portion of the macromolecule 
    
"""




from ViewerFramework.VFCommand import CommandGUI

from AutoDockTools.autoflexCommands import  AF_MacroReader,\
AF_MacroChooser, AF_SelectResidues, AF_ProcessResidues,\
AF_ProcessHingeResidues, AF_EditHinge, AF_SetHinge,\
AF_SetBondRotatableFlag, AF_StepBack, AF_FlexFileWriter,\
AF_RigidFileWriter, AF_LigandDirectoryWriter, menuText


AF_MacroReaderGUI=CommandGUI()
AF_MacroReaderGUI.addMenuCommand('AutoTools4Bar', menuText['AutoFlexMB'], \
        menuText['Read Macro'], cascadeName = menuText['InputMB'])

AF_MacroChooserGUI=CommandGUI()
AF_MacroChooserGUI.addMenuCommand('AutoTools4Bar', menuText['AutoFlexMB'],
            menuText['Choose Macro'], cascadeName = menuText['InputMB'])

AF_SelectResiduesGUI = CommandGUI()
AF_SelectResiduesGUI.addMenuCommand('AutoTools4Bar', menuText['AutoFlexMB'],menuText['Set Residues'])

AF_ProcessResiduesGUI = CommandGUI()
AF_ProcessHingeResiduesGUI = CommandGUI()

AF_EditHingeGUI = CommandGUI()
AF_EditHingeGUI.addMenuCommand('AutoTools4Bar', menuText['AutoFlexMB'],\
        menuText['Edit Hinge'])

AF_SetHingeGUI = CommandGUI()
AF_SetHingeGUI.addMenuCommand('AutoTools4Bar', menuText['AutoFlexMB'],\
        menuText['Set Hinge'])

AF_StepBackGUI = CommandGUI()
AF_StepBackGUI.addMenuCommand('AutoTools4Bar', menuText['AutoFlexMB'], menuText['Step Back'])

AF_FlexFileWriterGUI = CommandGUI()
AF_FlexFileWriterGUI.addMenuCommand('AutoTools4Bar', menuText['AutoFlexMB'], \
            menuText['writeFlexible'], cascadeName = menuText['WriteMB'])

AF_RigidFileWriterGUI = CommandGUI()
AF_RigidFileWriterGUI.addMenuCommand('AutoTools4Bar',  menuText['AutoFlexMB'], \
            menuText['writeRigid'], cascadeName = menuText['WriteMB'])

AF_LigandDirectoryWriterGUI = CommandGUI()
AF_LigandDirectoryWriterGUI.addMenuCommand('AutoTools4Bar', menuText['AutoFlexMB'], \
            menuText['writeDir'], cascadeName = menuText['WriteMB'])


commandList = [
    {'name':'AD4flex_readMacro','cmd':AF_MacroReader(),'gui':AF_MacroReaderGUI},
    {'name':'AD4flex_chooseMacro','cmd':AF_MacroChooser(),'gui':AF_MacroChooserGUI},
    {'name':'AD4flex_setResidues','cmd':AF_SelectResidues(),'gui':AF_SelectResiduesGUI},
    #{'name':'AD4flex_processResidues','cmd':AF_ProcessResidues(),'gui':None},
    #{'name':'AD4flex_processHingeResidues','cmd':AF_ProcessHingeResidues(),'gui':None},
    #{'name':'AD4flex_setBondRotatableFlag','cmd':AF_SetBondRotatableFlag(),'gui':None},
    #{'name':'AD4flex_setHinge','cmd':AF_SetHinge(),'gui':AF_SetHingeGUI},
    #{'name':'AD4flex_editHinge','cmd':AF_EditHinge(),'gui':None},
    {'name':'AD4flex_stepBack','cmd':AF_StepBack(),'gui':AF_StepBackGUI},
    {'name':'AD4flex_writeFlexFile','cmd':AF_FlexFileWriter(),'gui':AF_FlexFileWriterGUI},
    {'name':'AD4flex_writeRigidFile','cmd':AF_RigidFileWriter(),'gui':AF_RigidFileWriterGUI},
    #{'name':'AD4flex_writeFlexDir','cmd':AF_LigandDirectoryWriter(),'gui':AF_LigandDirectoryWriterGUI}
]

def initModule(vf):
    for dict in commandList:
        vf.addCommand(dict['cmd'], dict['name'], dict['gui'])
    if not hasattr(vf, 'ADflex_processResidues'):
        vf.addCommand(AF_ProcessResidues(), 'ADflex_processResidues', None)
    if not hasattr(vf, 'ADflex_setBondRotatableFlag'):
        vf.addCommand(AF_SetBondRotatableFlag(), 'ADflex_setBondRotatableFlag', None)
    vf.ADflex_setResidues = vf.AD4flex_setResidues
        
    
    if vf.hasGui:
        vf.GUI.menuBars['AutoTools4Bar'].menubuttons[menuText['AutoFlexMB']].config(bg='tan',underline='-1')    
        if not hasattr(vf.GUI, 'adtBar'):
            vf.GUI.adtBar = vf.GUI.menuBars['AutoTools4Bar']
            vf.GUI.adtFrame = vf.GUI.adtBar.menubuttons.values()[0].master



 



