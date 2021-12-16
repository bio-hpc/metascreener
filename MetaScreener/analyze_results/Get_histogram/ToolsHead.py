import os
from os.path import join
import sys
FOLDER_SHUTTLEMOL = 'MetaScreener'
GET_HISTOGRAM = join('analyze_results', 'Get_histogram/')
PYTHON_27_PACKAGES = join('external_sw', 'python2-packages/')
USED_SHUTTLEMOL = join('extra_metascreener', 'used_by_metascreener/')


PYTHON_RUN = "python"
with open("MetaScreener/config.cfg") as file:
    for line in file:
        if line.startswith("python_run"):
            PYTHON_RUN = line.strip().split(" ")[1]


def add_custom_python_paths():
    path_sm = os.path.dirname(__file__)[0:os.path.dirname(__file__).rfind(FOLDER_SHUTTLEMOL) + len(FOLDER_SHUTTLEMOL)]
    path_get_histogram = join(path_sm, GET_HISTOGRAM)
    path_extra_used = join(path_sm, PYTHON_27_PACKAGES)
    path_python_27_packages = join(path_sm, USED_SHUTTLEMOL)

    if 'PYTHONPATH' not in os.environ:
        os.environ['PYTHONPATH'] = ""
    for path in [path_get_histogram, path_extra_used, path_python_27_packages]:
        if path not in os.environ['PYTHONPATH']:
            os.environ['PYTHONPATH'] =  path+":" +os.environ['PYTHONPATH']
        if path not in sys.path:
            sys.path.insert(0,path)

