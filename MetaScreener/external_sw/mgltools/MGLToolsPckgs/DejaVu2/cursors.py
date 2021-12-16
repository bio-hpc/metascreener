#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2010
#
#############################################################################

#
# $Header: /opt/cvs/DejaVu2/cursors.py,v 1.1.1.1 2014/06/19 19:41:03 sanner Exp $
# 
# $Id: cursors.py,v 1.1.1.1 2014/06/19 19:41:03 sanner Exp $
#

import sys, os

## define cursors
cursorsDict = {
    'default':'',
    'busy':'watch',
    'None':'pirate',
    'default':'',
    'addToSelection':'',
    'removeFromSelection':'',
    'rotation':'exchange',
    'XYtranslation':'fleur',
    'Ztranslation':'double_arrow',
    'scale':'',
    'zoom':'sizing',
    'pivotOnPixel':'cross_reverse',
    'picking':'dotbox'
#    '':'',
    }

import DejaVu2
cpath = os.path.join(DejaVu2.__path__[0], 'Cursors')

if sys.platform=='linux2':
    cursorsDict['addToSelection'] = (
        '@'+os.path.join(cpath, 'AddSel.xbm'),
        os.path.join(cpath, 'AddSelMask.xbm'),
        'black', 'white')
    cursorsDict['removeFromSelection'] = (
        '@'+os.path.join(cpath, 'MinusSel.xbm'),
        os.path.join(cpath, 'MinusSelMask.xbm'),
        'black', 'white')
    cursorsDict['Ztranslation'] = (
        '@'+os.path.join(cpath, 'Ztrans.xbm'),
        os.path.join(cpath, 'ZtransMask.xbm'),
        'black', 'white')
elif os.name == 'nt':
    pass
    ## cursorsDict['None']='@'+os.path.join(cpath, 'NoAction.cur')
    ## cursorsDict['addToSelection']='@'+os.path.join(cpath, 'AddSel.cur')
    ## cursorsDict['removeFromSelection']='@'+os.path.join(cpath,
    ##                                                      'MinusSel.cur')
    ## cursorsDict['XYtranslation']='@'+os.path.join(cpath, 'XYtrans.cur')
    ## cursorsDict['Ztranslation']='@'+os.path.join(cpath, 'Ztrans.cur')

elif sys.platform=='darwin':
    cursorsDict['addToSelection'] = (
        '@'+os.path.join(cpath, 'AddSel.xbm'),
        os.path.join(cpath, 'AddSelMask.xbm'),
        'black', 'white')
    cursorsDict['removeFromSelection'] = (
        '@'+os.path.join(cpath, 'MinusSel.xbm'),
        os.path.join(cpath, 'MinusSelMask.xbm'),
        'black', 'white')
    cursorsDict['Ztranslation'] = (
        '@'+os.path.join(cpath, 'Ztrans.xbm'),
        os.path.join(cpath, 'ZtransMask.xbm'),
        'black', 'white')
    ## cursorsDict['None']='@'+os.path.join(cpath, 'NoAction.cur')
    ## cursorsDict['addToSelection']='@'+os.path.join(cpath, 'AddSel.cur')
    ## cursorsDict['removeFromSelection']='@'+os.path.join(cpath,
    ##                                                      'MinusSel.cur')
    ## cursorsDict['XYtranslation']='@'+os.path.join(cpath, 'XYtrans.cur')
    ## cursorsDict['Ztranslation']='@'+os.path.join(cpath, 'Ztrans.cur')
