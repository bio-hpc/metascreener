########################################################################
#
# Date: April 2006 Authors: Guillaume Vareille, Michel Sanner
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
#########################################################################
#
# $Header$
#
# $Id$
#

import types
import os
from ViewerFramework.VFCommand import CommandGUI

from Pmv.mvCommand import MVCommand
from DejaVu.colorMap import ColorMap
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.colorWidgets import PaletteChooser
from Pmv.colorPalette import ColorPalette,  ColorPaletteNG, ColorPaletteFunction, ColorPaletteFunctionNG

class EditColorPaletteByAtomType(MVCommand):

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('colorByAtomType'):
            self.vf.loadCommand('colorCommands', 'colorByAtomType', 'Pmv', topCommand = 0)
        self.vf.colorByAtomType.palette.read(os.path.join(self.vf.rcFolder,"colorByAtom_map.py"))


    def guiCallback(self):
        self.paletteGUI = PaletteChooser(apply_cb=self.apply, makeDefault_cb=self.doit, 
                                         restoreDefault_cb = self.restoreDefault,
                                         labels=self.vf.colorByAtomType.palette.labels, 
                                         ramp=self.vf.colorByAtomType.palette.ramp)

    def apply(self):
        ColorMap.configure(self.vf.colorByAtomType.palette, ramp=self.paletteGUI.ramp, 
                           labels=self.paletteGUI.labels)
        geoms = self.vf.colorByAtomType.getAvailableGeoms(self.vf.Mols)
        self.cleanup() #otherwise this was failing first time around
        self.vf.colorByAtomType(self.vf.Mols, geoms)

    def restoreDefault(self):
        try:
            os.remove(os.path.join(self.vf.rcFolder,"colorByAtom_map.py"))
        except:
            pass
        from Pmv.pmvPalettes import AtomElements
        self.vf.colorByAtomType.palette = ColorPalette('Atom Elements', colorDict=AtomElements,
                                    lookupMember='element')        
        geoms = self.vf.colorByAtomType.getAvailableGeoms(self.vf.Mols)
        self.cleanup() 
        self.vf.colorByAtomType(self.vf.Mols, geoms)
        # restore button color
        self.paletteGUI.setButtonsColor(self.vf.colorByAtomType.palette.ramp)
        
    def doit(self):
        self.vf.colorByAtomType.palette.configure(ramp=self.paletteGUI.ramp, labels=self.paletteGUI.labels)
        self.vf.colorByAtomType.palette.configureCmap()
        self.vf.colorByAtomType.palette.write(os.path.join(self.vf.rcFolder,"colorByAtom_map.py"))

        
EditColorPaletteByAtomTypeGUI = CommandGUI()
EditColorPaletteByAtomTypeGUI.addMenuCommand('menuRoot', 
                                             'Edit', 
                                             'Edit Color by Atom Type',
                                             cascadeName='Color Palettes')

class EditColorPaletteByResidueType(MVCommand):

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('colorByResidueType'):
            self.vf.loadCommand('colorCommands', 'colorByResidueType', 'Pmv', topCommand = 0)
        self.vf.colorByResidueType.palette.read(os.path.join(self.vf.rcFolder,"colorByResidueType_map.py"))


    def guiCallback(self):
        self.paletteGUI = PaletteChooser(apply_cb=self.apply, makeDefault_cb=self.doit, 
                                         restoreDefault_cb = self.restoreDefault,
                                         labels=self.vf.colorByResidueType.palette.labels, 
                                         ramp=self.vf.colorByResidueType.palette.ramp)


    def apply(self):
        ColorMap.configure(self.vf.colorByResidueType.palette, ramp=self.paletteGUI.ramp, 
                           labels=self.paletteGUI.labels)
        geoms = self.vf.colorByResidueType.getAvailableGeoms(self.vf.Mols)
        self.cleanup() #otherwise this was failing first time around
        self.vf.colorByResidueType(self.vf.Mols, geoms)

    def doit(self):
        self.vf.colorByResidueType.palette.configure(ramp=self.paletteGUI.ramp, labels=self.paletteGUI.labels)
        self.vf.colorByResidueType.palette.configureCmap()
        self.vf.colorByResidueType.palette.write(os.path.join(self.vf.rcFolder,"colorByResidueType_map.py"))

    def restoreDefault(self):
        try:
            os.remove(os.path.join(self.vf.rcFolder,"colorByResidueType_map.py"))
        except:
            pass
        from Pmv.pmvPalettes import RasmolAmino, RasmolAminoSortedKeys
        if self.vf.hasGui:
            paletteClass = ColorPalette
        else:
            paletteClass = ColorPaletteNG
        self.vf.colorByResidueType.palette = paletteClass(
            'RasmolAmino', RasmolAmino, readonly=0,
            sortedkeys = RasmolAminoSortedKeys, lookupMember='type')
        
        geoms = self.vf.colorByResidueType.getAvailableGeoms(self.vf.Mols)
        self.cleanup() 
        self.vf.colorByResidueType(self.vf.Mols, geoms)
        # restore button color
        self.paletteGUI.setButtonsColor(self.vf.colorByResidueType.palette.ramp)
        
EditColorPaletteByResidueTypeGUI = CommandGUI()
EditColorPaletteByResidueTypeGUI.addMenuCommand('menuRoot', 
                                             'Edit', 
                                             'Edit Color by Residue Type (Rasmol)',
                                             cascadeName='Color Palettes')

class EditColorPaletteByChain(MVCommand):

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('colorByChains'):
            self.vf.loadCommand('colorCommands', 'colorByChains', 'Pmv', topCommand = 0)
        self.vf.colorByChains.palette.read(os.path.join(self.vf.rcFolder,"colorByChain_map.py"))


    def guiCallback(self):
        self.paletteGUI = PaletteChooser(apply_cb=self.apply, makeDefault_cb=self.doit, 
                                         restoreDefault_cb = self.restoreDefault,
                                         labels=self.vf.colorByChains.palette.labels, 
                                         ramp=self.vf.colorByChains.palette.ramp)

    def apply(self):
        ColorMap.configure(self.vf.colorByChains.palette, ramp=self.paletteGUI.ramp, 
                           labels=self.paletteGUI.labels)
        geoms = self.vf.colorByChains.getAvailableGeoms(self.vf.Mols)
        self.cleanup() #otherwise this was failing first time around
        self.vf.colorByChains(self.vf.Mols, geoms)

    def restoreDefault(self):
        try:
            os.remove(os.path.join(self.vf.rcFolder,"colorByChain_map.py"))
        except:
            pass
        from mglutil.util.defaultPalettes import MolColors, Rainbow, RainbowSortedKey
        if self.vf.hasGui:
            paletteClass = ColorPaletteFunction
        else:
            paletteClass = ColorPaletteFunctionNG
        self.vf.colorByChains.palette = paletteClass(
            'MolColors', MolColors, readonly=0, 
            lookupFunction = lambda x, length = len(RainbowSortedKey):\
            x.number%length, sortedkeys = RainbowSortedKey)
        geoms = self.vf.colorByChains.getAvailableGeoms(self.vf.Mols)
        self.cleanup() 
        self.vf.colorByChains(self.vf.Mols, geoms)
        # restore button color
        self.paletteGUI.setButtonsColor(self.vf.colorByChains.palette.ramp)
        
    def doit(self):
        self.vf.colorByChains.palette.configure(ramp=self.paletteGUI.ramp, labels=self.paletteGUI.labels)
        self.vf.colorByChains.palette.configureCmap()
        self.vf.colorByChains.palette.write(os.path.join(self.vf.rcFolder,"colorByChain_map.py"))

EditColorPaletteByChainGUI = CommandGUI()
EditColorPaletteByChainGUI.addMenuCommand('menuRoot', 
                                             'Edit', 
                                             'Edit Color by Chain',
                                             cascadeName='Color Palettes')

class EditColorPaletteByMolecule(MVCommand):

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('colorByMolecules'):
            self.vf.loadCommand('colorCommands', 'colorByMolecules', 'Pmv', topCommand = 0)
        self.vf.colorByAtomType.palette.read(os.path.join(self.vf.rcFolder,"colorByMolecule_map.py"))

    def __call__(self, ramp, labels, **kw):
        """
None <- editPaletteByMolecule(self, colorDict, **kw)
"""
        #print "__call__"
        apply(self.doitWrapper, (ramp, labels), kw)


    def guiCallback(self):
        self.paletteGUI = PaletteChooser(apply_cb=self.apply, makeDefault_cb=self.doit, 
                                         restoreDefault_cb = self.restoreDefault,
                                         labels=self.vf.colorByMolecules.palette.labels, 
                                         ramp=self.vf.colorByMolecules.palette.ramp)

    def apply(self):
        ColorMap.configure(self.vf.colorByMolecules.palette, ramp=self.paletteGUI.ramp, 
                           labels=self.paletteGUI.labels)
        geoms = self.vf.colorByMolecules.getAvailableGeoms(self.vf.Mols)
        self.cleanup() #otherwise this was failing first time around
        self.vf.colorByMolecules(self.vf.Mols, geoms)
        
    def restoreDefault(self):
        try:
            os.remove(os.path.join(self.vf.rcFolder,"colorByMolecule_map.py"))
        except:
            pass
        from mglutil.util.defaultPalettes import MolColors, Rainbow, RainbowSortedKey
        c = 'Color palette molecule number'
        if self.vf.hasGui:
            paletteClass = ColorPaletteFunction
        else:
            paletteClass = ColorPaletteFunctionNG
        self.vf.colorByMolecules.palette = paletteClass(
            'MolColors', MolColors, readonly=0, info=c,
            lookupFunction = lambda x, length=len(RainbowSortedKey): \
            x.number%length, sortedkeys=RainbowSortedKey)
        geoms = self.vf.colorByMolecules.getAvailableGeoms(self.vf.Mols)
        self.cleanup() 
        self.vf.colorByMolecules(self.vf.Mols, geoms)
        # restore button color
        self.paletteGUI.setButtonsColor(self.vf.colorByMolecules.palette.ramp)
        

    def doit(self):
        self.vf.colorByMolecules.palette.configure(ramp=self.paletteGUI.ramp, labels=self.paletteGUI.labels)
        self.vf.colorByMolecules.palette.configureCmap()
        self.vf.colorByMolecules.palette.write(os.path.join(self.vf.rcFolder,"colorByMolecule_map.py"))

EditColorPaletteByMoleculeGUI = CommandGUI()
EditColorPaletteByMoleculeGUI.addMenuCommand('menuRoot', 
                                             'Edit', 
                                             'Edit Color by Molecule',
                                             cascadeName='Color Palettes')


class EditColorPaletteByInstance(MVCommand):

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('colorByInstance'):
            self.vf.loadCommand('colorCommands', 'colorByInstance', 'Pmv', topCommand = 0)
        self.vf.colorByAtomType.palette.read(os.path.join(self.vf.rcFolder,"colorByInstance_map.py"))

    def __call__(self, ramp, labels, **kw):
        """
        None <- editPaletteByInstance(self, colorDict, **kw)
        """
        #print "__call__"
        apply(self.doitWrapper, (ramp, labels), kw)


    def guiCallback(self):
        self.paletteGUI = PaletteChooser(apply_cb=self.apply, makeDefault_cb=self.doit, 
                                         restoreDefault_cb = self.restoreDefault,
                                         labels=self.vf.colorByInstance.palette.labels, 
                                         ramp=self.vf.colorByInstance.palette.ramp)

    def apply(self):
        ColorMap.configure(self.vf.colorByInstance.palette, ramp=self.paletteGUI.ramp, 
                           labels=self.paletteGUI.labels)
        geoms = self.vf.colorByInstance.getAvailableGeoms(self.vf.Mols)
        self.cleanup() #otherwise this was failing first time around
        self.vf.colorByInstance(self.vf.Mols, geoms)
        
    def restoreDefault(self):
        try:
            os.remove(os.path.join(self.vf.rcFolder,"colorByInstance_map.py"))
        except:
            pass
        from mglutil.util.defaultPalettes import MolColors, Rainbow, RainbowSortedKey
        c = 'Color palette molecule number'
        if self.vf.hasGui:
            paletteClass = ColorPaletteFunction
        else:
            paletteClass = ColorPaletteFunctionNG
        self.vf.colorByInstance.palette = paletteClass(
            'Rainbow', Rainbow, readonly=0, info=c,
            lookupFunction = lambda x, length=len(RainbowSortedKey): \
            x%length, sortedkeys=RainbowSortedKey)
        geoms = self.vf.colorByInstance.getAvailableGeoms(self.vf.Mols)
        self.cleanup() 
        self.vf.colorByInstance(self.vf.Mols, geoms)

    def doit(self):
        self.vf.colorByInstance.palette.configure(ramp=self.paletteGUI.ramp, labels=self.paletteGUI.labels)
        self.vf.colorByInstance.palette.configureCmap()
        self.vf.colorByInstance.palette.write(os.path.join(self.vf.rcFolder,"colorByInstance_map.py"))

EditColorPaletteByInstanceGUI = CommandGUI()
EditColorPaletteByInstanceGUI.addMenuCommand('menuRoot', 
                                             'Edit', 
                                             'Edit Color by Instance',
                                             cascadeName='Color Palettes')


commandList = [
    {'name':'editColorPaletteByAtomType', 
     'cmd':EditColorPaletteByAtomType(), 
     'gui':EditColorPaletteByAtomTypeGUI },
    {'name':'editColorPaletteByResidueType', 
     'cmd':EditColorPaletteByResidueType(), 
     'gui':EditColorPaletteByResidueTypeGUI },
    {'name':'editColorPaletteByChain', 
     'cmd':EditColorPaletteByChain(), 
     'gui':EditColorPaletteByChainGUI },          
    {'name':'editColorPaletteByMolecule', 
     'cmd':EditColorPaletteByMolecule(), 
     'gui':EditColorPaletteByMoleculeGUI },
    {'name':'editColorPaletteByInstance', 
     'cmd':EditColorPaletteByInstance(), 
     'gui':EditColorPaletteByInstanceGUI },
    ]


def initModule(viewer):
    for dict in commandList:
        viewer.addCommand( dict['cmd'], dict['name'], dict['gui'])
