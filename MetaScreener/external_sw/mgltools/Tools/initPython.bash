########
## if you plan to source this file from another directory, or from your shell
## ressource file use the commented out version
##
export MGL_ROOT="$(pwd)"
# export MGL_ROOT="/the/path/to/this/directory"

########
## plaform we run on
##
export MGL_ARCHOSV=`$MGL_ROOT/Tools/archosv`

########
## setting  MACOSX_DEPLOYMENT_TARGET var for MAC

if  test $MGL_ARCHOSV == 'ppcDarwin7'  | test  $MGL_ARCHOSV == 'ppcDarwin8'
then 
	export  MACOSX_DEPLOYMENT_TARGET="`/usr/bin/sw_vers | grep '^ProductVersion' | awk '{print substr($2,1,4)}'`"
fi

#######

## path to the extralibs directory.
##
export MGL_EXTRALIBS="$MGL_ROOT/$MGL_ARCHOSV/extralibs"

#######
## path to the extrainclude directory
export MGL_EXTRAINCLUDE="$MGL_ROOT/extrainclude"
########
## add the path to the directory holding the python interpreter to your path
##
export PATH="$MGL_ROOT/$MGL_ARCHOSV/bin:$PATH"

########
## define the PYTHONHOME environment variables
##
#export PYTHONHOME="$MGL_ROOT/share:$MGL_ROOT/$MGL_ARCHOSV"

########
## needed for Tkinter to find the Tcl/Tk libraries
##
export TCL_LIBRARY="$MGL_ROOT/tcl8.4"
export TK_LIBRARY="$MGL_ROOT/tk8.4"

########
## setup your LD_LIBRARY_PATH
##
shlibdirs="$MGL_ROOT/$MGL_ARCHOSV/lib:$MGL_ROOT/$MGL_ARCHOSV/extralibs"
if test -z "$LD_LIBRARY_PATH"
  then
    export LD_LIBRARY_PATH="$shlibdirs"
  else
    export LD_LIBRARY_PATH="$shlibdirs:$LD_LIBRARY_PATH"
 fi
