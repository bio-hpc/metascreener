#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2013
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/colorCmdsProxy.py,v 1.1 2014/06/05 23:40:33 annao Exp $
#
# $Id: colorCmdsProxy.py,v 1.1 2014/06/05 23:40:33 annao Exp $
#

def getGUI(GUITK):
    if GUITK=='Tk':
        from guiTK.colorCmds import ColorCommandGUI, ColorByAtomTypeGUI,\
             ColorByDGGUI, ColorByResidueTypeGUI, ColorShapelyGUI, \
             ColorByChainGUI, ColorByMoleculeGUI, ColorByInstanceGUI,\
             ColorByPropertiesGUI, RainbowColorGUI, RainbowColorByChainGUI,\
             ColorByExpressionGUI, ColorByLineGeometryColorGUI
        return {
            'color':[(ColorCommandGUI, (), {})],
            'colorByAtomType' :[(ColorByAtomTypeGUI, (), {})],
            'colorByResidueType' :[(ColorByResidueTypeGUI, (), {})],
            'colorAtomsUsingDG':[(ColorByDGGUI, (), {})],
            'colorResiduesUsingShapely' :[(ColorShapelyGUI, (), {})] ,
            'colorByChains' :[(ColorByChainGUI, (), {})],
            'colorByMolecules':[(ColorByMoleculeGUI, (), {})],
            'colorByInstance' :[(ColorByInstanceGUI, (), {})],
            'colorByProperty': [(ColorByPropertiesGUI, (), {})],
            'colorRainbow' : [(RainbowColorGUI, (), {})],
            'colorRainbowByChain' : [(RainbowColorByChainGUI,(), {})],
            'colorByExpression' : [(ColorByExpressionGUI, (), {})],
            'colorByLinesColor': [(ColorByLineGeometryColorGUI, (), {})]
            }
    elif GUITK=='Qt':
        return {}
    elif GUITK=='Wx':
        return {}
    else:
        return {'color':[(None, (), {})],
            'colorByAtomType' :[(None, (), {})],
            'colorByResidueType' :[(None, (), {})],
            'colorAtomsUsingDG':[(None, (), {})],
            'colorResiduesUsingShapely' :[(None, (), {})],
            'colorByChains' :[(None, (), {})],
            'colorByMolecules':[(None, (), {})],
            'colorByInstance' :[(None, (), {})],
            'colorByProperty': [(None, (), {})],
            'colorRainbow' : [(None, (), {})],
            'colorRainbowByChain' : [(None, (), {})],
            'colorByExpression' : [(None, (), {})],
            'colorByLinesColor': [(None, (), {})],
                }

commandsInfo = {
    'icoms' : {
        }
    }
