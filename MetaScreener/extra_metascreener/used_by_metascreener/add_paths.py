import os
import sys
FOLDER_SHUTTLEMOL = 'MetaScreener'
path_head = os.path.dirname(__file__)[0:os.path.dirname(__file__).rfind(FOLDER_SHUTTLEMOL) + len(FOLDER_SHUTTLEMOL)]
path_head = os.path.join(path_head, 'analyze_results', 'Get_histogram')
if path_head not in sys.path:
    sys.path.append(path_head)
from ToolsHead import *

def add_paths():
    add_custom_python_paths()