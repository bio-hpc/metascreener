mglroot = '/mnt/home/users/ac_001_um/jorgedlpg/pruebasDoking/SENECA/docking/mgltools_x86_64Linux2_latest'
# specify mglroot here
import sys, os
path = os.path.join(mglroot, "MGLToolsPckgs")
sys.path.append(path)

from os import getenv
if getenv('MGLPYTHONPATH'):
    sys.path.insert(0, getenv('MGLPYTHONPATH'))
    
from Support.path import setSysPath
setSysPath(path)
#sys.path.insert(0,os.path.abspath('.'))
