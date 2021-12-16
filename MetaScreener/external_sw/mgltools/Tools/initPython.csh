########
## if you plan to source this file from another directory, or from your shell
## ressource file use the commented out version
##
###

setenv MGL_ROOT `pwd`
# setenv MGL_ROOT /the/path/to/this/directory

########
## plaform we run on
##
setenv MGL_ARCHOSV `$MGL_ROOT/Tools/archosv`


########
## setting  MACOSX_DEPLOYMENT_TARGET var for MAC

if ($MGL_ARCHOSV == 'ppcDarwin7' || $MGL_ARCHOSV == 'ppcDarwin8' ) then 
	setenv MACOSX_DEPLOYMENT_TARGET `/usr/bin/sw_vers | grep '^ProductVersion' | awk '{print substr($2,1,4)}'`
endif
####

#######
## path to the extralib 
setenv MGL_EXTRALIBS $MGL_ROOT/$MGL_ARCHOSV/extralibs

#######
## path to the extrainclude
setenv MGL_EXTRAINCLUDE $MGL_ROOT/extrainclude

########
## add the path to the directory holding the python interpreter to your path
##
set path=( ${MGL_ROOT}/${MGL_ARCHOSV}/bin/ $path)

# DONE IN THE PMV, ADT and VISION SCRIPTS. (sophiec sept2004)
########
## define the PYTHONHOME environment variables
##
#setenv PYTHONHOME $MGL_ROOT/share:$MGL_ROOT/$MGL_ARCHOSV

########
## needed for Tkinter to find the Tcl/Tk libraries
##
setenv TCL_LIBRARY $MGL_ROOT/tcl8.4
setenv TK_LIBRARY $MGL_ROOT/tk8.4



########
## setup your LD_LIBRARY_PATH
##
if ( $?LD_LIBRARYN32_PATH ) then
    setenv LD_LIBRARYN32_PATH $MGL_ROOT/$MGL_ARCHOSV/lib:$MGL_ROOT/$MGL_ARCHOSV/extralibs:${LD_LIBRARYN32_PATH}
else if( $?LD_LIBRARYN64_PATH ) then
    setenv LD_LIBRARYN64_PATH $MGL_ROOT/$MGL_ARCHOSV/lib:$MGL_ROOT/$MGL_ARCHOSV/extralibs:${LD_LIBRARYN64_PATH}
else if ( $?LD_LIBRARY_PATH ) then
    setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:$MGL_ROOT/$MGL_ARCHOSV/lib:$MGL_ROOT/$MGL_ARCHOSV/extralibs
else
    setenv LD_LIBRARY_PATH $MGL_ROOT/$MGL_ARCHOSV/lib:$MGL_ROOT/$MGL_ARCHOSV/extralibs
endif
