#!/bin/csh
######
## Set some environment variables.
setenv MGL_ROOT

########
## plaform we run on
##
setenv MGL_ARCHOSV `$MGL_ROOT/bin/archosv`

#######
## path to the extralibs directory.
##
setenv MGL_EXTRALIBS $MGL_ROOT/lib

#######
## path to the extrainclude directory
setenv MGL_EXTRAINCLUDE $MGL_ROOT/include

########
## add the path to the directory holding the python interpreter to your path
##
set path=($MGL_ROOT/bin:$path)


setenv TCL_LIBRARY $MGL_ROOT/tcl8.4

setenv TK_LIBRARY $MGL_ROOT/tk8.4



# set the LD_LIBRARY PATH for each platform

if (`uname -s` == Darwin) then
    setenv DISPLAY :0.0
    # This will start X11 which provides windows system.
    # which is needed to run ADT/PMV and VISION
    echo "Starting X11"
    open -a X11
    set isdefined=`printenv DYLD_LIBRARY_PATH`
    if ( $#isdefined ) then
	setenv DYLD_LIBRARY_PATH $MGL_ROOT/lib:$DYLD_LIBRARY_PATH
    else
	setenv DYLD_LIBRARY_PATH $MGL_ROOT/lib
    endif

else
    set isdefined=`printenv LD_LIBRARY_PATH`
    if ( $#isdefined ) then
	setenv LD_LIBRARY_PATH $MGL_ROOT/lib:$LD_LIBRARY_PATH
    else
	setenv LD_LIBRARY_PATH $MGL_ROOT/lib
    endif

endif

# use python interpreter that comes with MGLTools

unset PYTHONHOME
setenv PYTHONHOME $MGL_ROOT
setenv PYTHONPATH $MGL_ROOT/MGLToolsPckgs
setenv python $MGL_ROOT/bin/python

