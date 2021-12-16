#!/bin/sh

# MGL Tools installation script
pythonargs=" "
pyoptimize=0
TarDir=`pwd`
export MGL_ROOT=""

# Parse the command-line arguments
opts=`getopt "hc:d:" "$@"`
if [ "$?" != 0 ]
then
   echo "Usage: source install.sh [-d InstDir] [-c optimization]"
   exit
fi
set -- $opts
while :
do
    case "$1" in 

    -c) shift; pythonargs="$pythonargs -c"; pyoptimize="$1";;
    -d) shift; export MGL_ROOT="$1";;
    -h) echo "Optional parameters:"
    echo "[-h]  help message;"
    echo "[ -d  InstDir] specifies installation directory (default-current directory)"
    echo "[ -c optimization] compile Python code with or without optimization:"
    echo "    0 - no optimization (generates .pyc files)"
    echo "    1 - with optimization (generates .pyo files);"
    exit ;;
    --) break;;
    esac
    shift
done


if [ "$MGL_ROOT" != "" ]; then
    # check if the user has write access to the installation directory
    if [ -e "$MGL_ROOT" ]; then
	if [ -d "$MGL_ROOT" ]; then
	    if [ ! -w  "$MGL_ROOT" ]; then 
		echo "Can not complete installation - specified directory $MGL_ROOT does not have write access."
		exit 1

	    fi
	else 
	    echo "$MGL_ROOT" is not a directory
	    exit 1
	fi
    else 
	echo Creating directory "$MGL_ROOT"
	mkdir "$MGL_ROOT"
    fi

else
    export MGL_ROOT="$(pwd)"
fi

echo "Installing MGLTools to $MGL_ROOT"

cd "$MGL_ROOT"
echo "Installing Python Interpreter to $MLG_ROOT"
tar xzvf $TarDir/Python*.tar.gz

if [ "$?" != 0 ]; then
    echo "Error in Python installation"
    exit 1
fi
echo Python installed, please wait for the rest of MGLTools to be installed 

cd $TarDir

## plaform we run on

export MGL_ARCHOSV=`$TarDir/Tools/archosv`

## add the path to the directory holding the python interpreter to your path

export PATH="$MGL_ROOT/bin:"$PATH

## use Python interpreter locally installed

PYTHON="$MGL_ROOT/bin/python"
export PYTHONHOME="$MGL_ROOT"
if [ "`uname -s`" = "Linux" ] ; then
    export LD_LIBRARY_PATH="$MGL_ROOT/lib"
fi

## run python script - install.py - to install MGL packages and create pmv , adt, and vision scripts

if [ "$pyoptimize" -eq 1 ]; then
    echo "Running $PYTHON -O Tools/install.py $pythonargs"
    $PYTHON -O Tools/install.py $pythonargs
else
    echo "Running $PYTHON Tools/install.py $pythonargs"
    $PYTHON Tools/install.py  $pythonargs
fi

unset PYTHONHOME
