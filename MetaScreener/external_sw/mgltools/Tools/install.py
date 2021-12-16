##
## Author: Michel F. Sanner, Sophie Coon, Anna Omelchenko
## Date: March 2003 revised: September 2004,July 2005, Jan 2006
## CopyRight: Michel F.SANNER and TSRI
##
##
import os, re, sys, string

#print "python executable", sys.executable
#print "prefix:", sys.prefix
#print "exec_prefix:", sys.exec_prefix

from os import path
import warnings
import tarfile
import compileall
from shutil import copy

compile = False
import getopt
optlist, pargs = getopt.getopt(sys.argv[1:], 'c')
if len(optlist):
    for opt in optlist:
        if opt[0] == "-c":
            compile = True

#
#print os.environ['PYTHONHOME']
# 
cwd = os.getcwd()
#print "current directory", cwd
mgl_root = path.abspath(os.environ['MGL_ROOT'])
mgl_archosv = os.environ['MGL_ARCHOSV']
bindir = path.join(mgl_root, 'bin')

#print "mgl_root", mgl_root
#print "mgl_archosv", mgl_archosv

# 1- Untar and install MGLPACKS
print 'Installing  MGLPackages'
py_version =  (string.split(sys.version))[0][0:3]
#print "python version:", py_version


scriptsInst = path.join(mgl_root, 'bin')

mglPckgsDir = 'MGLToolsPckgs'

mglTars = ['MGLToolsPckgs', 'Data', 'ThirdPartyPacks']

for name in mglTars:
    instDir = mgl_root
    if path.exists(name+'.tar.gz'):
        print "Installing files from %s " % name+'.tar.gz'
        # uncompress the tarFile
        tf = tarfile.open(name+'.tar.gz', 'r:gz')
        for tfinfo in tf:
            tf.extract(tfinfo, path=instDir)
        tf.close()

if compile: #compile Python source files to byte-code files
    try:
        compileall.compile_dir(path.join(mgl_root, "lib"))
    except:
        print "Compillation error"
        
# copy ./Tools/archosv to scriptsInst

copy(path.join("Tools", "archosv"), scriptsInst)

print "Creating the pmv, adt, vision and tester scripts"
# 2- Create the testersh, pmvsh. adtsh and visionsh script
templatePath = path.join(cwd, 'Tools/scriptTemplate')
f = open(templatePath, 'r')
tplLines = f.readlines()
f.close()

# Get the MGL_ROOT line
#l = filter(lambda x: x.startswith('MGL_ROOT='), tplLines)
l = [x for x in tplLines if x.startswith('MGL_ROOT=')]
if l:
    l = l[0]
    lIndex = tplLines.index(l)
    # set it to the right path
    tplLines[lIndex] = 'MGL_ROOT="%s" \n'%mgl_root

# Make pmv

pmvScript = path.join("$MGL_ROOT", mglPckgsDir,'Pmv','bin', 'runPmv.py' )
pmvlines = """if test $# -gt 0
then
	exec $python $pyflags %s $@
else
	exec $python $pyflags %s
fi
"""%(pmvScript, pmvScript)
pmvshPath = path.join(bindir, 'pmv')
f = open(pmvshPath, 'w')
f.writelines(tplLines)
f.write(pmvlines)
f.close()
os.chmod(pmvshPath, 509)

# Make pmv2 (for PmvApp)

pmv2Script = path.join("$MGL_ROOT", mglPckgsDir,'PmvApp', 'GUI', 'Qt', 'bin', 'runPmv.py' )
pmv2lines = """if test $# -gt 0
then
	exec $python $pyflags %s $@
else
	exec $python $pyflags %s
fi
"""%(pmv2Script, pmv2Script)
pmv2shPath = path.join(bindir, 'pmv2')
f = open(pmv2shPath, 'w')
f.writelines(tplLines)
f.write(pmv2lines)
f.close()
os.chmod(pmv2shPath, 509)

# Make epmv installation script

## epmvScript = path.join("$MGL_ROOT", mglPckgsDir,'Pmv','hostappInterface', 'install_plugin.py' )
## epmvlines = """if test $# -gt 0
## then
## 	exec $python $pyflags %s $@
## else
## 	exec $python $pyflags %s
## fi
## """%(epmvScript, epmvScript)
## epmvshPath = path.join(bindir, 'epmvInstall')
## f = open(epmvshPath, 'w')
## f.writelines(tplLines)
## f.write(epmvlines)
## f.close()
## os.chmod(epmvshPath, 509)


# Make adt

adtScript = path.join("$MGL_ROOT", mglPckgsDir, 'AutoDockTools','bin', 'runAdt.py' )
adtlines = """if test $# -gt 0
then
	exec $python $pyflags %s $@
else
	exec $python $pyflags %s
fi
"""%(adtScript, adtScript)
adtshPath = path.join(bindir, 'adt')
f = open(adtshPath, 'w')
f.writelines(tplLines)
f.write(adtlines)
f.close()
os.chmod(adtshPath, 509)


# Make vision

visionScript = path.join("$MGL_ROOT", mglPckgsDir, 'Vision','bin', 'runVision.py' )
visionlines = """if test $# -gt 0
then
	exec $python $pyflags %s $@
else
	exec $python $pyflags %s
fi
"""%(visionScript, visionScript)
visionshPath = path.join(bindir, 'vision')
f = open(visionshPath, 'w')
f.writelines(tplLines)
f.write(visionlines)
f.close()
os.chmod(visionshPath, 509)

# Make cadd

#caddScript = path.join("$MGL_ROOT", mglPckgsDir,'CADD','bin', 'runCADD.py' )
caddScript = path.join("$MGL_ROOT", mglPckgsDir,'CADD', 'Raccoon2', 'bin', 'raccoonLauncher' )
caddlines = """if test $# -gt 0
then
	exec $python $pyflags %s $@
else
	exec $python $pyflags %s
fi
"""%(caddScript, caddScript)
caddshPath = path.join(bindir, 'cadd')
f = open(caddshPath, 'w')
f.writelines(tplLines)
f.write(caddlines)
f.close()
os.chmod(caddshPath, 509)

#Make update

## updateScript = path.join("$MGL_ROOT", mglPckgsDir,'mglutil','TestUtil', 'bin', 'getlatest' )
## updatelines = """if test $# -gt 0
## then
## 	exec $python $pyflags %s $@
## else
## 	exec $python $pyflags %s
## fi
## """%(updateScript, updateScript)

## updateshPath = path.join(bindir,'getlatest')
## f = open(updateshPath, 'w')
## #f.writelines(tplLines[0:45])
## f.writelines(tplLines)
## f.write(updatelines)
## f.close()
## os.chmod(updateshPath, 509)

# Make tester

testerScript = path.join("$MGL_ROOT", mglPckgsDir,'mglutil','TestUtil', 'bin', 'tester' )
testerlines = """if test $# -gt 0
then
	exec $python $pyflags %s $@
else
	exec $python $pyflags %s
fi
"""%(testerScript, testerScript)
testershPath = path.join(bindir, 'tester')
f = open(testershPath, 'w')
f.writelines(tplLines)
f.write(testerlines)
f.close()
os.chmod(testershPath, 509)

# Make python executable
if sys.platform == 'darwin':
    #comment open -a X11
    #l = filter(lambda x: x.find('This assumes X11 is installed') != -1, tplLines)
    l = [x for x in tplLines if x.find('This assumes X11 is installed') != -1]
    if l:
        l = l[0]
        lIndex = tplLines.index(l)
        for i in range(1,10):
    	    tplLines[lIndex+i] = "#"+tplLines[lIndex+i]
    	    
pythonlines = """if test $# -gt 0
then
	exec $python $pyflags $@
else
	exec $python $pyflags 
fi
"""
pythonshPath = path.join(bindir, 'pythonsh')
f = open(pythonshPath, 'w')
f.writelines(tplLines)
f.write(pythonlines)
f.close()
os.chmod(pythonshPath, 509)

#create mglenv.sh and mglenv.csh files
mglenvshPath = path.join(bindir, 'mglenv.sh')
f = open(mglenvshPath , 'w')
f.writelines(tplLines)
f.close()
os.chmod(mglenvshPath, 509)


f = open(path.join(cwd, 'Tools/mglenv.csh'), 'r')
mglenvLines = f.readlines()
f.close()
# Get the MGL_ROOT line
#l = filter(lambda x: x.startswith('setenv MGL_ROOT'), mglenvLines)
l = [x for x in mglenvLines if x.startswith('setenv MGL_ROOT')]
if l:
    l = l[0]
    lIndex = mglenvLines.index(l)
    # set it to the right path
    mglenvLines[lIndex] = 'setenv MGL_ROOT %s\n'%mgl_root
mglenvcshPath = path.join(bindir, 'mglenv.csh')
f = open(mglenvcshPath , 'w')
f.writelines(mglenvLines)
f.close()
os.chmod(mglenvcshPath, 509)

# create mgl scripts to run OpenBabel executables
obexecs= ["babel", "obchiral", "obenergy",  "obgen", "obminimize",  "obprop", "obrotamer",  "obspectrophore", "obabel", "obconformer",  "obfit", "obgrep",  "obprobe", "obrms", "obrotate",   "roundtrip"]
templatePath = path.join(cwd, 'Tools/obscriptTemplate')
f = open(templatePath, 'r')
tplLines = f.readlines()
f.close()

# Get the MGL_ROOT line
l = [x for x in tplLines if x.startswith('MGL_ROOT=')]
if l:
    l = l[0]
    lIndex = tplLines.index(l)
    # set it to the right path
    tplLines[lIndex] = 'MGL_ROOT="%s" \n'%mgl_root

for obfile in obexecs:
    oblines = """obexec="$MGL_ROOT/bin/%s"\nexec $obexec  $@""" %(obfile,)
    obPath = path.join(bindir, "mgl%s"%obfile)
    f = open(obPath, 'w')
    f.writelines(tplLines)
    f.write(oblines)
    f.close()
    os.chmod(obPath, 509)


#create sitecustomize.py
f1 = open(os.path.join(mgl_root, mglPckgsDir, "Support", "sitecustomize.py"))
txt = f1.readlines()
f1.close()
f2 = open(os.path.join(mgl_root, "lib", "python%s"%py_version, "sitecustomize.py"), "w")
f2.write("mglroot = '%s'\n" % mgl_root)
if os.environ.has_key("MGL64"):
    f2.write("import os\n")
    f2.write("os.environ['MGL64']='1'\n")
f2.writelines(txt)
f2.close()

# check if initPython is sourced in your shell ressource file
#shell = sys.argv[1]
print "current directory:", os.getcwd()
alias_csh = """alias pmv %s/bin/pmv
alias adt %s/bin/adt
alias vision %s/bin/vision
alias cadd %s/bin/cadd
alias pythonsh %s/bin/pythonsh\n""" % (mgl_root, mgl_root,
                                           mgl_root, mgl_root, mgl_root)
alias_sh="""alias pmv='%s/bin/pmv'
alias adt='%s/bin/adt'
alias vision='%s/bin/vision'
alias cadd='%s/bin/cadd'
alias pythonsh='%s/bin/pythonsh'\n""" % (mgl_root, mgl_root,
                                           mgl_root, mgl_root, mgl_root)


f = open("initMGLtools.csh", "w")
f.write(alias_csh)
f.close()

f = open("initMGLtools.sh", "w")
f.write(alias_sh)
f.close()

#license part:

licensefile = os.path.join(mgl_root, mglPckgsDir, "mglutil", "splashregister", "license.py")

os.chdir(mgl_root)
#print "license part, current directory:", os.getcwd()

pythonscript = os.path.join(mgl_root, "bin", "pythonsh")
status = os.system("%s %s"%(pythonscript, licensefile))

print """\n MGLTools installation complete.
To run pmv, adt, vision or pythonsh scripts located at:
%s/bin
you will need to do ONE of the following:

-- add the %s/bin to the path environment variable in .cshrc or .bashrc:
.cshrc:
set path = (%s/bin $path)

.bashrc
export PATH=%s/bin:$PATH

-- create aliases in your .cshrc or .bashrc 
.cshrc:
alias pmv %s/bin/pmv
alias adt %s/bin/adt
alias vision %s/bin/vision
alias pythonsh %s/bin/pythonsh

.bashrc
alias pmv='%s/bin/pmv'
alias adt='%s/bin/adt'
alias vision='%s/bin/vision'
alias pythonsh='%s/bin/pythonsh'

-- source ./initMGLtools.sh (bash) or ./initMGLtools.csh (c-shell)

Please have a look at README file for more information about
licenses, tutorials, documentations and mailing lists for the different
packages enclosed in this distribution
If you have any problems please visit our FAQ page (http://mgltools.scripps.edu/documentation/faq).
"""%(mgl_root, 
     mgl_root,
     mgl_root,
     mgl_root,
     mgl_root, 
     mgl_root,
     mgl_root,
     mgl_root,
     mgl_root,
     mgl_root, 
     mgl_root,
     mgl_root
     )
