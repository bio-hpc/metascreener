#       
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli
#          Molecular Graphics Lab
#  
#     The Scripps Research Institute 
#           _  
#          (,)  T  h e
#         _/
#        (.)    S  c r i p p s
#          \_
#          (,)  R  e s e a r c h
#         ./  
#        ( )    I  n s t i t u t e
#         '
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

"""
Collection of helper functions used in different code for Virtual Screening and
other applications


Index:

 = PDB/Atom stuff




 = Numeric stuff

 = OS stuff


 = Geometry stuff

 = Tk Stuff

 = Constants

v.0.6
v.0.7 modified Xmas
v.0.8 modified in Jan 2012 for Waters support
"""


from Tkinter import *
from numpy import *
from math import fabs, acos, degrees, sqrt, e
from glob import glob
from string import strip
import os, getopt, re, fnmatch
import string
import zlib
import json, marshal
import tarfile
import urllib2
import hashlib
from sys import exc_info
try:
    import VolumeOperators.trilinterp as ti # XXX PMV dependency!
    import Volume.Operators as tp
except:
    print "WARNING! VOLUME OPERATORS ARE NOT AVAILABLE (we're not in an MGL-python)"
import Pmw
import platform


###############################################
############  CONSTANTS  ######################
###############################################

# CONSTANTS
PI  = 3.14159
PI2 = PI*2
# from AD4_parameter.dat Rii/2 values
vdw_radii = { 'H': 1.00, 'HD': 1.00, 'HS': 1.00, 'C': 2.00,
    'A': 2.00, 'N': 1.75, 'NA': 1.75, 'NS': 1.75, 'OA': 1.60,
    'OS': 1.60, 'F': 1.54, 'Mg': 0.65, 'MG': 0.65, 'P': 2.10,
    'SA': 2.00, 'S': 2.00, 'Cl': 2.04, 'CL': 2.04, 'Ca': 0.99,
    'CA': 0.99, 'Mn': 0.65, 'MN': 0.65, 'Fe': 0.65, 'FE': 0.65,
    'Zn': 0.74, 'ZN': 0.74, 'Br': 2.165, 'BR':2.165, 'I':2.36,
    'Z' : 2.00, 'G' : 2.00, 'GA': 2.00, 'J' :2.00, 'Q' :2.00,
    'X': 2 } # default vdW for unknown atom



# actual vdw radii THE OVER THERE IS DIAMETER!!!
vdwRadii = { 'A' : 1.00, 'BR' : 1.08, 'Br' : 1.08, 'C' : 1.00,
    'CA' : 0.49, 'CL' : 1.02, 'Ca' : 0.49, 'Cl' : 1.02,
    'F' : 0.77, 'FE' : 0.33, 'Fe' : 0.33, 'G' : 1.00,
    'GA' : 1.00, 'H' : 0.50, 'HD' : 0.50, 'HS' : 0.50,
    'I' : 1.18, 'J' : 1.00, 'MG' : 0.33, 'MN' : 0.33,
    'Mg' : 0.33, 'Mn' : 0.33, 'N' : 0.88, 'NA' : 0.88,
    'NS' : 0.88, 'OA' : 0.80, 'OS' : 0.80, 'P' : 1.05,
    'Q' : 1.00, 'S' : 1.00, 'SA' : 1.00, 'X' : 1.00,
    'Z' : 1.00, 'ZN' : 0.37, 'Zn' : 0.37,
    'X' : 1.5 } # default vdW for unknown atom





bond_lenghts_sq = { 'A' : 1.00, 'C' : 1.00, 'MN' : 0.11, 'GA' : 1.00,
                'Zn' : 0.14, 'F' : 0.59, 'ZN' : 0.14, 'H' : 0.25, 'CA' : 0.25,
                'Mn' : 0.11, 'Mg' : 0.11, 'N' : 0.77, 'Q' : 1.00, 'P' : 1.10,
                'S' : 1.00, 'FE' : 0.11, 'BR' : 1.17, 'X' : 1.00, 'Z' : 1.00,
                'HD' : 0.25, 'MG' : 0.11, 'G' : 1.00, 'Cl' : 1.04, 
                'NA' : 0.77, 'Ca' : 0.25, 'CL' : 1.04, 'OA' : 0.64,
                'I' : 1.39, 'Fe' : 0.11, 'Br' : 1.17, 'HS' : 0.25,
                'SA' : 1.00, 'NS' : 0.77, 'OS' : 0.64, 'J' : 1.00,
                }


bond_lenghts = { 'A' : 1.00, 'C' : 1.00, 'MN' : 0.33,
        'GA' : 1.00, 'Zn' : 0.37, 'F' : 0.77,
        'ZN' : 0.37, 'H' : 0.50, 'CA' : 0.49,
        'Mn' : 0.33, 'Mg' : 0.33, 'N' : 0.88,
        'Q' : 1.00, 'P' : 1.05, 'S' : 1.00,
        'FE' : 0.33, 'BR' : 1.08, 'X' : 1.00,
        'Z' : 1.00, 'HD' : 0.50, 'MG' : 0.33,
        'G' : 1.00, 'Cl' : 1.02, 'NA' : 0.88,
        'Ca' : 0.49, 'CL' : 1.02, 'OA' : 0.80,
        'I' : 1.18, 'Fe' : 0.33, 'Br' : 1.08, 
        'HS' : 0.50, 'SA' : 1.00, 'NS' : 0.88, 
        'OS' : 0.80, 'J' : 1.00,
        }


adtypes = {  # count  MW
    'H'   : [ 0,  1    ],
    'HD'  : [ 0,  1    ],
    'HS'  : [ 0,  1    ],
    'C'   : [ 0,  12   ],
    'A'   : [ 0,  12   ],
    'N'   : [ 0,  14   ],
    'NA'  : [ 0,  14   ],
    'NS'  : [ 0,  14   ],
    'OA'  : [ 0,  16   ],
    'OS'  : [ 0,  16   ],
    'F'   : [ 0,  19   ],
    'Mg'  : [ 0,  24   ],
    'MG'  : [ 0,  24   ],
    'P'   : [ 0,  31   ],
    'SA'  : [ 0,  32   ],
    'S'   : [ 0,  32   ],
    'Cl'  : [ 0,  35.4 ],
    'CL'  : [ 0,  35.4 ],
    'Ca'  : [ 0,  40   ],
    'CA'  : [ 0,  40   ],
    'Mn'  : [ 0,  55   ],
    'MN'  : [ 0,  55   ],
    'Fe'  : [ 0,  56   ],
    'FE'  : [ 0,  56   ],
    'Zn'  : [ 0,  65.4 ],
    'ZN'  : [ 0,  65.4 ],
    'Br'  : [ 0,  80   ],
    'BR'  : [ 0,  80   ],
    'I'   : [ 0, 126   ],
    'e'   : [ 1,   0   ], # always 1 by default
    'd'   : [ 1,   0   ]  # always 1 by default
        }


ignore_at = [ 'HD', 'H', 'W' ] # TODO experimental, to allow handling special atoms, like waters


METALS = [ 'Mg', 'MG', 'Ca', 'CA', 'Mn', 'MN', 'Fe', 'FE', 'Zn', 'ZN' ]


HCOVBOND = 1.1



# functional stuff and tricks

class QuickStop:
    """empty class used to trigger an except
       to speed up checks (try/except VS if/then)
    """
    pass



###############################################
#############  ATOM STUFF #####################
###############################################


def pmvAtomStrip(atom, mol_name = None):
    """ transform PDB(QT) atoms to PMV syntax
      "ATOM    455  N   GLY A  48      -2.978   5.488   6.818  1.00 11.64    -0.351 N" (xJ1_xtal)
            |
           \./
            '  
       xJ1_xtal:A:GLY48:N
    """
    chain = atom[21].strip()
    res_name = atom[16:21].strip()
    res_num = atom[22:26].strip()
    atom = atom[12:16].strip()
    if not mol_name:
        return "%s:%s%s:%s" % (chain, res_name, res_num, atom)
    else:
        return "%s:%s:%s%s:%s" % (mol_name, chain, res_name, res_num, atom)


"""
def matchThisInteraction(entry1, entry2, strict=True, DEBUG=False):
    "" "checks if entry1 is equal or a subset of entry2
    Allowed syntax entries are:
        CHAIN:RES:AT
        CHAIN:RES
        :RES:AT
        :RES
    "" "
    # TODO XXX XXX XXX XXX XXX 
    #  add dictionary sets for residue types:
    #  polar-uncharged
    #  positively charged AA
    #  negatively charged
    #  aromatic 
    # 
    # XXX XXX XXX XXX XXX
    # entry1 = ":TYR12:"
    # entry2 = "A:TYR12:O"


    # XXX XXX very fragile! warning with Pi interactions
    # B:PHE149~~(66.904,71.516,40.205:70.416,70.616,38.595) <-- no atom level!


    if DEBUG:
        print "E1:", entry1
        print "E2:", entry2
    parts = entry1.count(":")
    if parts == 2:      # vdw, hb, metal  (D:DA17:N1)
        chain1, res1, at1 = entry1.split(":")
    elif parts == 1:    # pi interaction  (A:MG396:MG)
        chain1, res1 = entry1.split(":")
        at1 = ""
    chain2, res2, at2 = entry2.split(":")
    #chain2, res2 = entry2.split(":")
    if DEBUG: 
        print "chain, res, at: comparing..."
        print "|%s:%s:%s|" %(chain1, res1, at1),
        print "|%s:%s:%s|" %(chain2, res2, at2),
    if strict:
        if not chain1 or chain1 == chain2:
            if not res1 or res1 == res2:
                if not at1 or at1 == at2:
                    if DEBUG: print "[strict] found!"
                    return True
    else:
        if not chain1 or chain1 == chain2: # NOTE one letter...
            if not res1 or res1 in res2:
                if not at1 or at1 in at2:
                    if DEBUG: print "[no-strict] found!"
                    return True
    
    return False
"""


def isAtom(l):
    return l.startswith("ATOM") or l.startswith("HETATM")


def getCoords(alist, include_hydrogens = True):
    """ 
    fast extraction of atoms from a PDBQT 
    return { text : org_ascii_lines, coords : numpy_array, atype : atypes_strings }
    NOTE if idrogens are excluded "text" and "coords" lenght will mismatch!
    """
    coord = []
    atoms = []
    atype = []
    for l in alist:
        #if l.startswith("ATOM") or l.startswith("HETATM"):
        if isAtom(l):
            #at = l.rsplit(None, 1)[1]
            at = l.rsplit(None, 1)[1]
            at = getAtype(l)
            if not at == "HD" or include_hydrogens: # by default, HD are included
                coord.append([float(l[30:38]),float(l[38:46]),float(l[46:54])])
                #coord.append([atomCoord(l)]) # TODO test if this can do the trick... from atomCoord()
                atype.append(at) 
            atoms.append(l.strip())
    return { 'text' : atoms, 'coord' : array( coord, 'f'), 'atype': atype }

def getFlatAtoms(ligand, flat_only = True, skip_hd = True):
    # XXX the returned value order should be changed to match
    # XXX getCoords... text, coord, atype ?
    # used for getting ligand atoms, usually only flat ones
    # for aromatic rings detection
    flatland = [ "A", "OA", "NA", "N", "SA"]
    hydrogens = ['HD', 'H']
    data = []
    atoms = getAtoms(ligand)
    for l in atoms:
        #if l.startswith("ATOM") or l.startswith("HETATM"):
        atype = getAtype(l)
        if not atype in hydrogens:
            if (atype in flatland) or (not flat_only):
                data.append([atype, atomCoord(l), l])
        elif not skip_hd:
            data.append([atype, atomCoord(l), l])
    return data

def findHbAccepDon(atom_list):
    """identifies HB donors and acceptors in a list of PDBQT atoms
       returns : acceptors[] and donors[] lists
    """
    H_COV_BOND = 1.1  
    H_COV_BOND  = H_COV_BOND ** 2  
    acceptor_types = ['OA', 'NA', 'SA']
    donor_types = ['N', 'O', 'OA', 'NA', 'SA']
    acceptors = []
    donors = []
    h = []
    dcandidate = []
    for l in atom_list:
        if l.startswith("ATOM") or l.startswith("HETATM"):
            l = l.strip()
            atype=l.split()[-1]
            if atype in acceptor_types:
                if not l in acceptors:
                    acceptors.append(l)
            elif atype in donor_types:
                if not l in dcandidate:
                    dcandidate.append(l)
            elif atype == 'HD':
                if not l in h:
                    h.append(l)
    for a in dcandidate:
        for x in h:
            if dist(a, x) <= H_COV_BOND:
                donors.append(a)
                break
    return acceptors, donors 





def getAtoms(ligand, atomOnly=False, hetOnly=False): 
    """ in :  PDBQT
        out:  ATOM/HETATM entries    
    """
    atoms=[]
    hetatm=[]
    for l in ligand:
        if l.startswith("ATOM"):
            atoms.append(l)
        elif l.startswith("HETATM"):
            hetatm.append(l)
    if atomOnly: return atoms
    elif hetOnly: return hetatm
    else: return atoms+hetatm




def atomCoord(a): # works with pdb atoms
    """return atom coords from a single PDB[QT] line"""
    #return map(float, [a[30:38], a[38:46], a[46:54]]) ### TEST Wednesday, April 25 2012
    return  array(  [a[30:38], a[38:46], a[46:54]], 'f')
    coord = map(float, [a[30:38], a[38:46], a[46:54]]) ### TEST Wednesday, April 25 2012
    return array( coord, 'f')

def getPdbOccupancy(a):
    """ return pdb atom occupancy"""
    try:
        return float(a[60:67])
    except:
        return 0.0

def avgAtoms(atom_list):
    atom_list = map(atomCoord, atom_list)
    return avgCoord(atom_list)

def avgCoord(atom_list): # TODO change this to become avgAtomCoord
    """returns the average coordinates from a list of PDB(QT) atoms or coordinates"""
    avg = [0., 0., 0.,]
    #print "GOT ATOM LIST", atom_list
    c = float(len(atom_list))
    for a in atom_list:
        if type(a) == type("a"):
            a = atomCoord(a)
        avg[0] += a[0]
        avg[1] += a[1]
        avg[2] += a[2]
    return array([ avg[0]/c, avg[1]/c, avg[2]/c ], 'f')



def clusterAtoms(atoms, tol=2.0):
    """  atoms [x,y,x,z,y,z,x, ...] =>  [ [x,x,x], [y,y], [ z,z,z,z,z,z,z,z], ... ] 
    
        input: PDBQT lines atoms
    """
    tol = tol**2
    atom_clusters = []
    used = []
    while len(atoms)>1:
        def func(x): return dist(atoms[0], x, sq=False) <= tol
        cluster = filter(func, atoms[1:]) + [atoms[0]]
        reminder = []
        for a in atoms: # XXX use a set here?
            if not a in cluster:
                reminder.append(a)
        atoms = reminder[:]
        atom_clusters.append(cluster)
    if atoms:
        atom_clusters.append(atoms)
    #return atom_clusters
    return sorted(atom_clusters, key=len, reverse=True)



def makePdb(coord, keyw = "ATOM  ", at_index = 1, res_index = 1, atype = 'X', elem = None,
            res = "CNT", chain  ="Z", bfactor = 10,pcharge = 0.0):
    if not elem: elem = atype
    # padding bfactor
    bfactor = "%2.2f" % bfactor
    if len(bfactor.split(".")[0]) == 1:
        bfactor = " "+bfactor
    # ORG:
    #atom = "%s%5d  %2s  %3s %1s%4d    %8.3f%8.3f%8.3f  1.00 %02.2f  %8.3f %1s" % (keyw,
    atom = "%s%5d  %2s  %3s %1s%4d    %8.3f%8.3f%8.3f  1.00 %s  %8.3f %1s" % (keyw,
            at_index, elem, res, chain, res_index, 
            coord[0], coord[1], coord[2], bfactor, pcharge, atype)
    #print atom
    return atom


def isValidPDBQTplus(f, mode='autodock'):
    FP = open(f,'r')
    l = FP.readline()
    FP.close()
    if mode=='autodock':
        if l.startswith("USER    ADVS_result>"): return True
    elif mode=='vina':
        if l.startswith("USER    ADVS_Vina_result>"): return True
    return false
        
def isValidVinaResult(f):
    FP = open(f,'r')
    l = FP.readlines(1)
    FP.close()
    if l.startswith("REMARK VINA RESULT:"):return True
    return False


def getPDBQTroot(ligand):
    """
    isolate and return the atoms defining the ROOT entity
    in an AutoDock/Vina PDBQT file
    """
    inside=False
    root=[]
    #for l in ligand:
    #    print l

    for l in ligand:
        if l.startswith('ENDROOT'): 
            #print "going out"
            #for x in root:
            #    print x
            return root    
        if inside: 
            #print "APPENDING"
            root.append(l)
        if l.startswith('ROOT'): 
            #print "we're inside"
            inside=True


# XXX OLD MODEL
"""
def getModel(ligand, model=None):
    #print "[ CALLED WITH MODEL=%s ]" % model
    poses = []
    inside=False
    for l in ligand:
        if inside: tmp.append(l)
        if l.startswith('MODEL'):
            tmp=[]
            inside=True
        if l.startswith('ENDMDL'):
            poses.append(tmp)
            inside=False
    if len(poses)==0:
        #print "PROBLEM HERE!!!"
        return 
    if len(poses)==1:
        #print "POSES UNIQUE",
        return poses[0]
    if model == None:
        #print "ASKING EVERYTHING ?!?!?!",model,
        return poses
    else:
        try:
            #print "MODEL REQUESTED",model
            return poses[model]
        except:
            #print "MODEL DEFAULT 0"
            return poses[0]
"""


def getModel(ligand, model=None):
    #print "[ CALLED WITH MODEL=%s ]" % model
    poses = []
    inside=False
    for l in ligand:
        if inside: tmp.append(l)
        if l.startswith('MODEL'):
            tmp=[]
            inside=True
        if l.startswith('ENDMDL'):
            poses.append(tmp)
            inside=False
    if len(poses)==0:
        print "PROBLEM HERE!!!"
        return 
    #if len(poses)==1:  # XXX DISABLED! INCONSISTENT
    #    #print "POSES UNIQUE",
    #    return poses[0]
    if model == None:
        #print "ASKING EVERYTHING ?!?!?!",model,
        return poses
    else:
        try:
            #print "MODEL REQUESTED",model
            return poses[model]
        except:
            #print "MODEL DEFAULT 0"
            return poses[0]



def isMultiModelPdb(ligand):
    for l in ligand:
        if l.startswith('MODEL'):
            return True
    return False

def getDockedLigandCentroid(ligand, model=None, pdb=True, bfactor=10):
    pose = getModel(ligand,model=model)
    #pose = getModel(ligand,model=0)
    #print "==POSE LEN", len(pose)
    root=getPDBQTroot(pose)
    centroid=avgCoord(root)
    if pdb: return makePdb(centroid, bfactor=bfactor)+"\nTER\n"
    else: return centroid


def getReceptorResidues(filename=None, data=None):
    """Accepts a PDB(TQ) file and returns a 
       nested dictionary of:
        
           chain:residue:atoms

    """
    if filename:
        lines = getLines(filename)
    else:
        lines = data
    structure = {}
    for l in lines:
        if l.startswith("ATOM") or l.startswith("HETATM"):
            res_t=l[17:20].strip()
            res_n=l[22:27].strip()
            res=res_t+res_n
            chain=l[21].strip()
            atom=l[12:17].strip()
            if not chain in structure:
                structure[chain]={}
            if not res in structure[chain]:
                structure[chain][res] = []
            if not atom in structure[chain][res]:
                structure[chain][res].append(atom)
    return structure


def getAtype(a):
    # returns PDB(QT) atom type
    #return a.rsplit(None, 1)[1].strip() 
    return a[77:79].strip()


# numeric stuff

def frange(start, end=None, step=1):

    if end == None:
        end = float(start)
        start = 0.
    else:
        start = float(start)
        end == float(end)
    
    total = int((float(end)-float(start))/float(step))
    #print total
    c = 1
    out = [start]
    while  c < total:
        c+=1
        out.append( start + c*step)
        #if c > 100:
        #    break
    #print len(out)
    return out
        
        
        



def map2array(data):
    """ autogrid map (text list) to NumpyArray """

    # grid spacing
    spacing = float(data[3].split()[1])

    # grid size 
    pts = data[4].split()[1:]
    for i in range(len(pts)):
        pts[i] = float(pts[i])+1
    # grid center
    center = data[5].split()[1:]
    for i in range(len(pts)):
        center[i] = float(center[i])
    # grid points
    data = data[6:]
    #for i in range(len(data)):
    #    data[i] = float(data[i])
    data = map(float, data) # USELESS? # XXX done anyway later by array

    # x,y,z steps
    step = [ pts[0]/2 * spacing, pts[1]/2 * spacing, pts[2]/2 * spacing ]
    # min, max coord values of the box
    v_min = [ center[0]-step[0], center[1]-step[1], center[2]-step[2] ]
    v_max = [ center[0]+step[0], center[1]+step[1], center[2]+step[2] ]

    data = array(data, 'f').reshape(pts[2], pts[1], pts[0])
    return { "values" : data, "spacing" : spacing, 'pts': pts, 'center' : center, 'min' : v_min, 'max' : v_max}


def getInterpolMapValue( ptlist, gridvalues, origin, invstep=None, spacing=None):
    # INCOMPLETE! XXX XXX XXX
    """ ptlist  :   numpy.array of pt coordinates for which interpolated 
                    values must be calculated
        gridmap :   numpy.array of map points (i.e. grid['values'] generated with map2array)
        origin  :   minimum x,y,z coords

        spacing :   gridmap 'resolution' 
        invstep :   1./ grid spacing (3-tuple)

            (either one of the two can be specified)
    """
    if not spacing == None:
        invstep = ( 1./ spacing, 1./spacing, 1./spacing )
    
    return ti.trilinterp(ptlist, gridvalues, invstep, origin)

def generateInterpolMap( gridmap, newspacing, agformat=True):
    # XXX INCOMPLETE!
    newgrid = {}
    newgrid['min'] = grid['min']
    newgrid['max'] = grid['max']
    newgrid['center'] = grid['center']
    newgrid['spacing'] = newspacing

    space_ratio = spacing / gridmap['spacing']
    pts = gridmap['pts']
    newpts = [ int(x*space_ratio) for x in pts ]
    for i in range(len(newpts)):
        if not newpts[i] % 2 == 0:
            newpts[i] -=1
        #newgrid['values'] # XXX ADD THIS? and remove below?
    newgrid['pts'] = newpts


    ptlist = []
    for z_incr in range( newpts[2]+1 ): #XXX remove the +1 ?
        for y_incr in range( newpts[1]+1):
            for x_incr in range( newpts[0]+1):
                pt = [ vmin[0] + (x_incr*newspacing),
                       vmin[1] + (y_incr*newspacing),
                       vmin[2] + (z_incr*newspacing),
                     ]
                ptlist.append(pt)
    origin = gridmap['min']
    values = getInterpolMapValues(ptlist, gridmap['values'], gridmap['spacing'])
    if agformat:
        values = values.reshape(newpts[2]+1, newpts[1]+1, newpts[0]+1)
    newgrid['values'] = values
    return newgrid


def writeAutoGridMap( gridmap={}, filename=None, agformat = 1, gpfname = 'gpf.gpf', recname = 'protein'):
    header = ( "GRID_PARAMETER_FILE %s\n",
               "GRID_DATA_FILE %s.maps.fld\n",
               "MACROMOLECULE %s.pdbqt\n",
               "SPACING %1.3f\n",
               "NELEMENTS %d %d %d\n",
               "CENTER %2.3f %2.3f %2.3f\n",
               )
   
    #info = header % (gpfname, recname, recname, gridmap['spacing'], 
    #          gridmap['pts'][0], gridmap['pts'][1], gridmap['pts'][2],
    #          gridmap['center'][0], gridmap['center'][1],gridmap['center'][2])

    info = "XXXX"
    print "X", len(gridmap['values'])
    print "Y", len(gridmap['values'][0])
    print "Z", len(gridmap['values'][0][0])
    fp = open(filename, 'w')
    fp.write(info)
    if agformat:
        for z in range(gridmap['pts'][2]):
            for y in range(gridmap['pts'][1]):
                for x in range(gridmap['pts'][0]):
                    print gridmap['values'][x][y][z]
                    fp.write('%1.5f\n'% gridmap['values'][x][y][z])
                    #except:
                    #    print "ERROR", x,y,z, sys.exc_info()[1]
    else:
        for v in gridmap:
            fp.write('%1.5\n'% v)
            
    fp.close() 




def gpf2pdb(input_file, output_file=None, atype = 'Fe', center=False):
    # XXX This should become 2 separate functions!
    """ Convert AutoGrid GPF to PDB.
        Points order in the PDB is the following:

            8 ______ 7
             /.    /|
          4 /_.___/3|
            | . X | |  <-- 9
            |5....|./6
            |.____|/
           1      2

    """
    GPF = getLines(input_file)
    if not output_file:
        output_file = input_file.replace('.gpf', '_BOX.pdb')
    for line in GPF:
        if len(line) > 3:
            tmp=line.split()
            if tmp[0] == "gridcenter":
                center_x = float(tmp[1])
                center_y = float(tmp[2])
                center_z = float(tmp[3])
            if tmp[0] == "npts":
                pts_x = float(tmp[1])
                pts_y = float(tmp[2])
                pts_z = float(tmp[3])
            if tmp[0] == "spacing":
                res = float(tmp[1])
    step_x = pts_x/2 * res
    step_y = pts_y/2 * res
    step_z = pts_z/2 * res
    Max = [ center_x+step_x,center_y+step_y,center_z+step_z]
    Min = [ center_x-step_x,center_y-step_y,center_z-step_z]
    pdb_out = []
    pdb_out.append("REMARK   Generated from : %s " % input_file)
    corners = []
    # 1 
    corners.append([ center_x - step_x, center_y - step_y, center_z - step_z] )
    # 2
    corners.append([ center_x + step_x, center_y - step_y, center_z - step_z] )
    # 3
    corners.append([ center_x + step_x, center_y + step_y, center_z - step_z] )
    # 4
    corners.append([ center_x - step_x, center_y + step_y, center_z - step_z] )
    # 5 
    corners.append([ center_x - step_x, center_y - step_y, center_z + step_z] )
    # 6
    corners.append([ center_x + step_x, center_y - step_y, center_z + step_z] )
    # 7
    corners.append([ center_x + step_x, center_y + step_y, center_z + step_z] )
    # 8
    corners.append([ center_x - step_x, center_y + step_y, center_z + step_z] )
    count = 1
    res = "BOX"
    chain = "X"
    for i in range(len(corners)):
        x = corners[i][0]
        y = corners[i][1]
        z = corners[i][2]
        pdb_out.append( makePdb(coord=(x,y,z), keyw="ATOM  ",
            at_index = count,atype=atype, res=res, chain=chain))
        count += 1

    # center
    if center:
        pdb_out.append( makePdb( (center_x,center_y,center_z),
            res=res,chain=chain,atype=atype, index=count))
    pdb_out.append("CONECT    1    2")
    pdb_out.append("CONECT    1    4")
    pdb_out.append("CONECT    1    5")
    pdb_out.append("CONECT    2    3")
    pdb_out.append("CONECT    2    6")
    pdb_out.append("CONECT    3    4")
    pdb_out.append("CONECT    3    7")
    pdb_out.append("CONECT    4    8")
    pdb_out.append("CONECT    5    6")
    pdb_out.append("CONECT    5    8")
    pdb_out.append("CONECT    6    7")
    pdb_out.append("CONECT    7    8")

    if output_file:
        #print "gpf2pdb> writing to",output_file
        writeList(output_file, pdb_out, addNewLine=True)
    else: return pdb_out

def makePdbBox(center = [], size = [], corners = [], atype = 'Fe', centerpt = 0, buff=0.0):
    if not size:
        if not corners:
            print "Need size or corners! exiting"
            return
        size = []
        size.append( corners[0][1]- corners[0][0] )
        size.append( corners[1][1]- corners[1][0] )
        size.append( corners[2][1]- corners[2][0] )
    step_x = (size[0]+buff)/2.
    step_y = (size[1]+buff)/2.
    step_z = (size[2]+buff)/2.
    Max = [ center[0]+step_x,center[1]+step_y,center[2]+step_z]
    Min = [ center[0]-step_x,center[1]-step_y,center[2]-step_z]
    pdb_out = []
    pdb_out.append("REMARK   BOX ")

    points = []
    # 1 
    points.append([ center[0] - step_x, center[1] - step_y, center[2] - step_z] )
    # 2
    points.append([ center[0] + step_x, center[1] - step_y, center[2] - step_z] )
    # 3
    points.append([ center[0] + step_x, center[1] + step_y, center[2] - step_z] )
    # 4
    points.append([ center[0] - step_x, center[1] + step_y, center[2] - step_z] )
    # 5 
    points.append([ center[0] - step_x, center[1] - step_y, center[2] + step_z] )
    # 6
    points.append([ center[0] + step_x, center[1] - step_y, center[2] + step_z] )
    # 7
    points.append([ center[0] + step_x, center[1] + step_y, center[2] + step_z] )
    # 8
    points.append([ center[0] - step_x, center[1] + step_y, center[2] + step_z] )
    count = 1
    res = "BOX"
    chain = "X"
    for i in range(len(points)):
        x = points[i][0]
        y = points[i][1]
        z = points[i][2]
        pdb_out.append( makePdb(coord=(x,y,z), keyw="ATOM  ",
            at_index = count,atype=atype, res=res, chain=chain))
        count += 1

    # center point
    if centerpt:
        pdb_out.append( makePdb( (center[0],center[1],center[2]),
            res=res,chain=chain,atype=atype, at_index=count))
    pdb_out.append("CONECT    1    2")
    pdb_out.append("CONECT    1    4")
    pdb_out.append("CONECT    1    5")
    pdb_out.append("CONECT    2    3")
    pdb_out.append("CONECT    2    6")
    pdb_out.append("CONECT    3    4")
    pdb_out.append("CONECT    3    7")
    pdb_out.append("CONECT    4    8")
    pdb_out.append("CONECT    5    6")
    pdb_out.append("CONECT    5    8")
    pdb_out.append("CONECT    6    7")
    pdb_out.append("CONECT    7    8")
    return pdb_out



def boundingBox(atoms, tol=0.0):
    """ atoms is [PDB atoms] 
    """
    xmin = 9e10
    xmax = -9e10
    ymin = 9e10
    ymax = -9e10
    zmin = 9e10
    zmax = -9e10
    for a in atoms:
        coord = atomCoord(a)
        x = coord[0]
        y = coord[1]
        z = coord[2]

        xmin = min(x, xmin)
        ymin = min(y, ymin)
        zmin = min(z, zmin)

        xmax = max(x, xmax)
        ymax = max(y, ymax)
        zmax = max(z, zmax)

    #center = avgCoord(atoms)
    center = [ (xmax+xmin)/2, (ymax+ymin)/2, (zmax+zmin)/2 ]
    ddd= { 'x': [ xmin-tol, xmax+tol ],
           'y': [ ymin-tol, ymax+tol ],
           'z': [ zmin-tol, zmax+tol ],
           'center':center }
    return ddd

def getLigAbout(filename):
    # calculate the mean position of ATOM/HETATM lines
    # inside a ROOT/ENDROOT in a PDBQT file
    x,y,z  = 0., 0., 0.
    counter = 0
    IN = False
    for l in getLines(filename):
        if IN:
            if l[0:6] == 'HETATM' or l[0:4] == 'ATOM':
                counter += 1
                x += float(l[30:38])
                y += float(l[38:46])
                z += float(l[46:54])
        if l.startswith('ROOT'):
            IN = True
        elif l.startswith('ENDROOT'):
            return [x/counter, y/counter, z/counter]



def getGpfData(filename, debug=0):
    """ read data from a GPF and return a dictionary """
    for l in getLines(filename):
        l = l.strip()
        if l:
            # remove comment
            l = l.split("#", 1)[0]
            l = l.split(" ", 1)
            kw = l[0].strip()
            arg = l[1].strip()
            if kw == "gridcenter":
                arg = arg.split()
                #center = map(float, arg[0], arg[1], arg[2])
                center = map(float, arg)
            elif kw == "npts":
                arg = arg.split()
                #pts = map(float, arg[0], arg[1], arg[2])
                pts = map(float, arg)
            elif kw == "spacing":
                res = float(arg)
            elif kw == 'smooth':
                smooth = float(arg)
            elif kw == 'dielectric':
                dielectric = float(arg)

    step  = [pts[0]/2*res, pts[1]/2*res, pts[2]/2*res]
    g_max = [center[0]+step[0], center[1]+step[1], center[2]+step[2]]
    g_min = [center[0]-step[0], center[1]-step[1], center[2]-step[2]]
    return {'center':center,'pts':pts,'res':res,
            'step':step,'g_max':g_max, 'g_min':g_min,
            'smooth': smooth, 'dielectric': dielectric}
    
def getDpfData(filename, debug=0):
    """ parse a DPF file, identify the search mode
        return a dictionary with the settings
    
        the dictionary structure respects the one 
        defined in the Raccon2_AutoDockManager.py
    """
    dpf_parms = { 

            'search_mode'   : None,
            'runs'          : None,
            'do_clustering' : None,

            'generic' : [ 'autodock_parameter_version',
                          'parameter_file',
                          'outlev',
                          'intelec',
                          'seed',
                          'unbound_model'],

            'ga' : [ 'ga_pop_size',
                     'ga_num_evals',
                     'ga_num_generations',
                     'ga_elitism',
                     'ga_mutation_rate',
                     'ga_crossover_rate',
                     'ga_window_size',
                     'ga_cauchy_alpha',
                     'ga_cauchy_beta',
                     'set_ga'],

            'sa': [ 'tstep',
                    'qstep',
                    'dstep',
                    'rt0',
                    'scheduler',
                    'rtrf',
                    'trnrf',
                    'quarf',
                    'dihrf',
                    'cycles',
                    'accs',
                    'rejs',
                    'select'],

            'ls' : [ 'ga_pop_size',
                     'sw_max_its',
                     'sw_max_succ',
                     'sw_max_fail',
                     'sw_rho',
                     'sw_lb_rho',
                     'ls_search_freq',
                     'set_psw1'],

        'clustering': [ 'rmstol', 'analysis'],
            }


    search_specific = { 'ga_run' :  [ 'search_mode', 'lga' ],
                        'do_global_only': ['search_mode', 'ga'],
                        'do_local_only': ['search_mode', 'ls'],
                        'simanneal' : ['search_mode', 'sa'],
                        'analysis' : ['do_clustering', True],

                        }
    run_setting = ['ga_run', 'do_global_only', 'do_local_only', 'simanneal']

    def _findtype(kw):
        for t in dpf_parms.keys():
            if dpf_parms[t] and kw in dpf_parms[t]:
                return t
        return False

    lines = getLines(filename)
    dpf = {}
    search = None
    for l in lines:
        l = l.strip()
        if l:
            used = False
            l = l.split("#", 1)[0]
            l = l.split(" ", 1)
            kw = l[0].strip()
            arg = l[1].strip()
            parm_type = _findtype(kw)
            if not parm_type:
                if kw in search_specific.keys():
                    settnval = search_specific[kw]
                    dpf[settnval[0]] = settnval[1]
                    used = True
                if kw in run_setting:
                    dpf['run'] = arg
                    used = True
            else:
                if not parm_type in dpf.keys():
                    dpf[parm_type] = {}
                dpf[parm_type][kw] = arg
                used = True
            if not used and debug: 
                print "getDpfData> ignored kw [%s]" % kw
    return dpf


def getVinaConfData(filename):
    """ get data from a Vina config file and return a dict"""
    conf = { 'rec' : None,
             'lig' : None,
             'center_x' : None,
             'center_y' : None,
             'center_z' : None,
             'size_x' : None,
             'size_y' : None,
             'size_z' : None,
             'cpu'  : None,
             'flex' : None,
             'out'  : None,
             'seed' : None,
             'exhaustiveness' : None,
             'num_modes' : None,
             'energy_range': None,
             }

    convert = { 'rec' : str,
              'lig' : str,
              'center_x' : float,
              'center_y' : float,
              'center_z' : float,
              'size_x' : float,
              'size_y' : float,
              'size_z' : float,
              'cpu' : int,
              'flex': str,
              'out': str,
              'seed': float,
              'exhaustiveness' : int,
              'num_modes': int,
              'energy_range': float,
              }

    data = getLines(filename)
    is_valid = False
    for l in data:
        l = l.strip()
        if l :
            l = l.split('=')
            kw = l[0].strip()
            arg = l[1].strip()
            if kw in conf.keys():
                conf[kw] = convert[kw](arg)
                is_valid = True
    if is_valid:
        return conf
    else:
        return False
        

def getPdbqtTors(filename):
    """ parse ligand and flexres PDBQT for TORSDOF keyword(s)
        
        return total TORSDOF
    """
    tors = 0
    lines = getLines(filename)
    for l in lines:
        if l.startswith('TORSDOF'):
            tors += int(l.split("TORSDOF")[1])
    return tors


def pdbinthebox(filename, gpf=None, max_coords=None, fullRes=False,
            min_coords=None, output=None, dtol=0.0):
    """ accepts a PDB(QT) file and returns
        only atoms that are contained in the given set of coordinates
    """
    if (gpf == None) and (max_coords==None or min_coords==None):
        print "ERROR: either GPF or coords required."
        return False

    if gpf:
        gpf_data = getGpfData(gpf)
        max_coords = gpf_data['g_max']
        min_coords = gpf_data['g_min']

    if output==None:
        output = os.path.splitext(filename)[0]+'_IN_THE_BOX.pdbqt'

    inputdata = getLines(filename)
    PDB_OUT = []
    res_list = []
    ASP=False
    head= 'REMARK   Receptor atoms: %s\n' % filename
    if gpf:
        head+='REMARK   contained in coords defined in %s' % gpf
    else:
        head+='REMARK   contained in coords Min(%s), Max(%s)' % ( str(max_coords), str(min_coords))
    for line in inputdata:
        if line[0:4] == "ATOM" or line[0:6] == "HETATM":
            x,y,z = atomCoord(line)
            res = pmvAtomStrip(line).rsplit(":",1)[:-1]
            if x < max_coords[0]+dtol and x > min_coords[0]-dtol:
                if y < max_coords[1]+dtol and y > min_coords[1]-dtol:
                    if z < max_coords[2]+dtol and z > min_coords[2]-dtol:
                        PDB_OUT.append(line)
                        if not res in res_list: res_list.append(res)
    if fullRes:
        for line in inputdata:
            if line[0:4] == "ATOM" or line[0:6] == "HETATM":
                res = pmvAtomStrip(line).rsplit(":",1)[:-1]
                if res in res_list:
                    if not line in PDB_OUT:
                        PDB_OUT.append(line)


    writeList(output,PDB_OUT,addNewLine=True)
    return output


def atominthebox(atomlist, coord_min, coord_max, tol=0.0):
    accepted = []
    for a in atomlist:
        x,y,z = atomCoord(a)
        if x < coord_max[0]+tol and x > coord_min[0]+tol:
            if y < coord_max[1]+tol and y > coord_min[1]+tol:
                if z < coord_max[2]+tol and z > coord_min[2]+tol:
                    accepted.append(a)
    return accepted


def getHistogram(filename):
    """extract the histogram fingerprint from a PDBQT+ file"""
    lines = getLines(filename)
    pattern = "USER    AD_histogram> "
    for l in lines:
        if pattern in l:
            l = l.split(pattern)[1]
            return l.split(",")
    return False





# generic stuff


def stripDlgTime(line, type = 'real'):
    locations  ={ "real" : 0,
                "cpu"  : 1,
                "sys"  : 2}
    h = 0
    m = 0
    s = 0
    line = line.split(",")[ locations[type] ]
    line = line.split("=")[1]
    try:
        h,reminder = line.split("h", 1)
    except:
        reminder = line
    try:
        m,reminder = reminder.split("m", 1)
    except:
        pass
    s = reminder.split("s",1)[0]
    h = float(h)*3600
    m = float(m)*60
    s = float(s)
    return h+m+s






def whichFile(filename):
    """ provide same functionalities as the Unix command
        'which', returning the full path of a given
        filename/command
    """
    for path in os.environ["PATH"].split(os.pathsep):
        exe_file = os.path.join(path, filename)
        if is_exe(exe_file):
            return exe_file
    return False
    #        if CheckExe(exe_file):
    #            AutoGridBin.set(os.path.normpath(exe_file))
    #            AutoGridExecButton.config(text = "Change AutoGrid executable", fg = 'black')
    #            TheCheck()
    #            return True



def splitdir(count, total, step):
    """generate a name for splitting many items by a given step.
        example:
            - 1200 items
            - divide 100 items per dir

            generate a "00", "01" names series

    """
    zeropadding = "%%0%dd" % len(str(total/step))
    suffix = zeropadding % (count/step)
    return suffix


def removeEmptyLines(lines):
    print "\n#########################################"
    print "HelperFunctionsN3P> OBSOLETE!!! removeEmptyLines: UPDATE THE CODE AND REMOVE IT"
    print "##########################################\n"
    data = []
    for l in lines:
        if l.strip():
            data.append(l)
    return data

def getLines(filename, doStrip = False, removeEmpty=False):
    """ """
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    if doStrip: 
        lines = map(strip,lines)
    if removeEmpty:
        #lines = removeEmptyLines(lines)
        lines = [ l for l in lines if l.strip() ]
    return lines


def jsonhelper(data):
    """provide decoding functions to restore python
       types from json files
    """
    def _decode_list(data):
        rv = []
        for item in data:
            if isinstance(item, unicode):
                item = item.encode('utf-8')
            elif isinstance(item, list):
                item = _decode_list(item)
            elif isinstance(item, dict):
                item = _decode_dict(item)
            rv.append(item)
        return rv

    def _decode_dict(data):
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
               key = key.encode('utf-8')
            if isinstance(value, unicode):
               value = value.encode('utf-8')
            elif isinstance(value, list):
               value = _decode_list(value)
            elif isinstance(value, dict):
               value = _decode_dict(value)
            rv[key] = value
        return rv

    #def _decode_data(data):
    if isinstance(data, list):
        return _decode_list(data)
    elif isinstance(data, dict):
        return _decode_dict(data)    


def readjson(fname, compression=False, convert=True):
    """ read and parse json files """
    fp = open(fname, 'rb')
    data = fp.read()
    fp.close()
    if len(data):
        if compression:
            data = zlib.decompress(data)
        if convert:
            return json.loads( data, object_hook = jsonhelper)
        else:
            return json.loads( data)
    else:
        return False

def writejson(fname, data, compression=False):
    """ write (compressed) json files """

    print "*" * 50
    print data
    print "*" * 50
    #json.encoder.FLOAT_REPR = lambda o: format(o, '.2f')
    fp = open(fname, 'wb')
    data = normalizeJsonData(data)
    if compression :
        out = json.dumps(data)
        out = zlib.compress(out)
        fp.write(out)
    else:
        json.dump(data, fp)
    fp.close()


def normalizeJsonData(data):
    """ """
    if isinstance(data, tuple):
        data = list(data)
    if isinstance(data, dict):
        for k,v in data.items():
            if isinstance(v, dict) or isinstance(v,list) or isinstance(v,tuple):
                v = normalizeJsonData(v)
            data[k] = v
    elif isinstance(data, list):# or isinstance(data,tuple):
        for i,v in enumerate(data):
            if isinstance(v, dict) or isinstance(v,list) or isinstance(v,tuple):
                v = normalizeJsonData(v)
            elif isinstance(v, float):
                v = '%.3f' % v
            data[i] = v
    return data


def writemarshal(fname, data, compression=False):
    """ write marshalized file"""
    fp = open(fname,'wb')
    if compression:
        out = marshal.dumps(data)
        out = zlib.compress(out)
        fp.write(out)
    else:
        marshal.dump(data, fp)
    fp.close()

def readmarshal(fname, compression=False):
    """ read marshalized file"""
    fp = open(fname, 'rb')
    data = fp.read()
    fp.close()
    if len(data):
        if compression:
            data = zlib.decompress(data)
        return marshal.loads( data)



def hashfile(afile, hasher=hashlib.md5(), blocksize=65536):
    """ generate a fingerprint of the input file provided
        and return a hex string writable as text
        (i.e., "0147b763f093825a06259ce10d5613f3")

        by default the hashlib.md5() hasher is used,
        but all hashlib hashers are supported

        afile can be a file object handle or a filename
    """
    if isinstance(afile, str):
        try:
            afile = open(afile, 'r')
        except:
            print "HASHFILE ERROR", sys.exc_info()[1]
            return False
    buff = afile.read(blocksize)
    while len(buff) > 0:
        hasher.update(buff)
        buff = afile.read(blocksize)
    return hasher.hexdigest()


def downloadfile(url, localdirectory='.', localfile=None):
    """use urllib2 to download a remote link to a file
    
        by default try to guess the local filename to be used

    """
    if localfile == None:
        try:
            localfile = url.rsplit('/', 1)[1]
        except:
            print "something funky with the URL [%s], better using localfile (RETURNING)"
            return False, 'impossible to guess localfile name'
    localfile = localdirectory + os.sep + localfile
    try:
        response = urllib2.urlopen(url)
    except:
        err = sys.exc_info()[1]
        print "ERROR accessing url [%s] : [%s]" % (url, err)
        return False, err
    try:
        fp = open(localfile, 'wb')
        fp.write(response.read())
        fp.close()
        return True, localfile
    except:
        err = sys.exc_info()[1]
        print "ERROR saving localfile [%s] : [%s]" % (localfile, err)
        return False, err

    


def makeDir(path=None, name=None, fullpath=None, checkexist=True):
    """ create dir for the generation process"""
    #print "path", path
    #print "name",name

    if fullpath:
        dirname = fullpath
    else:
        dirname = path + os.sep + name
    if os.path.isdir(dirname) and checkexist:
        print "directory [%s] exist, passing silently as requested" % dirname
        return
    try:
        os.makedirs(dirname)
        return dirname
    except:
        print "makeDir> ERROR creating dir [%s]: %s" % (dirname, exc_info()[1])
        return False


def touch(fname):
    """create a zero lenght file (unix touch)"""
    try:
        open(fname, 'w').close()
        return True
    except:
        return sys.exc_info()[1]




def tarextract(tarfilename, filelist=[], outdir=None, mode='r'):
    """ if empty filelist is requested, all files will be extracted
    
        by default the file is opened in transparent read mode
        use mode=xx to force

        if filelist is provided, files that are found in the tar 
        are extracted with their basename in the specified path:

                /usr/bin/ls -> ls
    """
    # extracting files from tar file
    print "EXTRACTING FILES FROM TAR"
    files = []
    try:
        ext = os.path.splitext(tarfilename)[1]
        tar = tarfile.open(tarfilename, mode)
    except:
        print "TAR ERROR(1)", sys.exc_info()[1]
        return False, sys.exc_info()[1]

    if len(filelist):
        # extracting requested files
        #print "EXTRACTING REQUESTED FILES"
        try:
            for tfile in tar.getmembers():
                #print "CHECKING TAR FILE", tfile, tfile.name
                for f in filelist:
                    #print "AGAINST", f
                    #print tfile.name.rsplit('/',1)[1], f,  tfile.name.rsplit('/',1)[1]==f
                    if '/' in tfile.name: 
                        name = tfile.name.rsplit('/',1)[1]
                    else:
                        name = tfile.name
                    #print "CHECKING", name, f, name == f
                    if name == f:
                        #print "FOUND FILE", f
                        buff = tar.extractfile(tfile).read()
                        outfname = outdir + os.sep + f
                        fp = open(outfname, 'wb')
                        fp.write(buff)
                        fp.close()
                        files.append(outfname)
            tar.close()
        except:
            print "TAR ERROR(2)", sys.exc_info()[1]
            return False, sys.exc_info()[1]
    else:
        # extracting all 
        #print "EXTRACTING ALL"
        try:
            tar.extractall(path=outdir)
            files = [ outdir + os.sep + f for f in tar.getmembers() ]
        except:
            print "TAR ERROR(3)", sys.exc_info()[1]
            return False, sys.exc_info()[1]
    #print "FILES EXTRACTED", files
    return True, files



def writeList(filename, inlist, mode = 'w', addNewLine = False):
    if addNewLine: nl = "\n"
    else: nl = ""
    fp = open(filename, mode)
    for i in inlist:
        fp.write(str(i)+nl)
    fp.close()


def readString(filename):
    f = open(filename, 'r')
    string = f.read()
    f.close()
    return string

def percent(value, total):
    if total==0 or value ==0: return 0
    return (float(value)/float(total))*100


def gaussian(x, ymax = 1, center=0, spread=0.7):
    return ymax * e **( -((float(x)-center)**2/ (2*spread**2) ) )



def truncateName(s,
            lmax,            # max chars before start truncating
            ellipses='...',  # separator
            lpad=3,          # left padding chars (before ellipses)
            rpad=3,          # right padding chars (after ellipses)
            auto=True):      # guess the padding
    if len(s)<=lmax or len(s) < lpad+rpad:
        return s
    else: 
        if auto:
            currLen = len(s)
            lmax = lmax - len(ellipses)
            rpad = lpad = lmax / 2
            if lpad + rpad < lmax:
                rpad += 1
            return s[:lpad] + ellipses + s[-rpad:]
        return s[:lpad]+ellipses+s[-rpad:]


def listToString(inlist, sep=', ', wide=10):
    """ format a list into a string with
        lines containing 'wide' items
    """
    c = 0
    text = ''
    itemlist = range(len(inlist))
    for i in itemlist:
        item = inlist[i]
        if c == wide:
            text +='\n'
            c=0
        text += str(item)
        c+=1
        if not i == itemlist[-1]:
            text += sep
    return text
        



"""
#### REMOVED WITH THE NEXT ONE... TESTING THAT THEN REMOVE THIS
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def pathToList(path, recursive = False, pattern = "", extension = ""):
    ""- given a path, returns all files matching  a given pattern ("_OUT") 
       or an extension (i.e. ".dlg").
       - if no pattern nor extension are specified, all files will be returned
       - if (recursive == True), it scans also subfolders
            Examples:
                   pattern   =  "_OUT", "_HIV_", "_VS.pdbqt"
                   extension = ".pdbqt", ".dlg"

        NOTE: Extension has priority on Pattern!
    ""
    def _matchpattern(pattern, text):
        
        print "PATT, TEXT", pattern,text
        return re.search(pattern, text)
            

    if not recursive:
        #matching_files = glob(os.path.join(path, "*"+extension))
        #matching_files = filter(lambda x: pattern in x, matching_files)
        matching_files = glob(os.path.join(path, pattern+"*"+extension))
    else:
        matching_files = []
        for root, subFolders, files in os.walk(path):
            for fname in files:
                if _matchpattern(pattern, fname):
                    if extension:
                        name, ext = os.path.splitext(fname)
                        if ext == extension:
                          
 
 
 
 
 
 
 

   matching_files.append(os.path.join(root,fname))
                    else:
                        matching_files.append(os.path.join(root,fname))
    return matching_files
"""


def pathToList(path, pattern="*", recursive=False, extension = None, GUI = None, GUIvar=None, 
        stopcheck=None): #, resultvar = None): #, donefunc = None):
    """ find all files matching pattern in path, (OPT: recursively) 
        GUIvar is a Tk variable that can be set with:

            GUIvar.set(value)
    
    """ 
    #print "CALLED PATHTOLIST", path, pattern, recursive, extension
    #if not resultvar == None:
    #    result = resultvar
    #else:
    result = []
    if GUI:
        c = 0 # update gui each 10 steps
    if recursive:
        path = os.path.normpath(path)
        path = os.path.expanduser(path)
        for dirpath, dirnames, filenames in os.walk(path):
            if not stopcheck == None:
                if stopcheck():
                    break
            if not GUI == None:
                GUI.update()
                if not GUIvar == None:
                    GUIvar.set( truncateName( dirpath, lmax=40) )
                if c == 9:
                    GUI.update_idletasks()
                    c = 0
                else:
                    c += 1 
            result.extend(os.path.join(dirpath,f) for f in fnmatch.filter(filenames,pattern))
    else:
        result = glob(os.path.join(path, pattern))
    #print "FOUND %d RES" % len(result)
    #if not donefunc == None:
    #    donefunc()
    #if resultvar == None:
    return result


def findLigandsInDlg(dlg_list, checkSuccess=True, showprogress=True):
    """
    scan DLG files for the lig name (AD 'move' kw); by default checks that calculation
    has been successful.

    if showprogress is set to True, a spinning ascii art is shown 
    and updated each 5 files
    """
    import sys
    progress = "-\|/"
    ligands = {}
    problematic = []
    error = None
    c = 0
    t = 0
    tot = len(dlg_list)
    for f in dlg_list:
        t += 1
        try:
            lines = getLines(f)
            for l in lines:
                if l.startswith("DPF> move"):
                    l = l.split("DPF> move", 1)[1].split(".pdbqt")[0]
                    success = True
                    if checkSuccess and not "Successful" in lines[-5]:
                        error = "Docking not successful"
                        break
                    if not l in ligands:
                        ligands[l] = [f]
                    else:
                        ligands[l].append(f)
                    break
        except:
            error = sys.exc_info()[1]
        if not error == None:
            problematic.append([f, error])
        c +=1
        if showprogress:
            if c == 5:
                print "\r%s scanning for mol names [ %d | %d ]          " % (progress[0], t, tot),
                c = 0
                sys.stdout.flush()
                progress = progress[1:] + progress[0]
    return ligands, problematic



def alternative_pathToList(path, pattern='*', recursive=False): # XXX TMP TEMP XXX
    """ """
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches




def checkPdbqtList(filelist):
    """ 
        check if the file is a valid AutoDock(Vina) file (mode):
            - 'lig' : formatted ligand file
            - 'rec' : target structure file
            - 'flex': formatted flexible residue(s)
        return dictionary { lig, rec, flex, error}
    """
    lig = []
    rec = []
    flex = []
    error = []
    for f in filelist:
        found = None
        try:
            data = getLines(f)
            for l in data:
                if l.startswith('BEGIN_RES'):
                    found = 'flex'
                    flex.append(f)
                    break
                elif l.startswith('ROOT'):
                    found = 'lig'
                    lig.append(f)
                    break
                elif l.startswith('ATOM') or l.startswith('HETATM'):
                    found = 'rec'
                    rec.append(f)
                    # if no keywords have been found so far
                    # a PDBQT can be only a rec file
                    break
        except: 
            found = 'file_error [%s]: %s' % (f, exc_info()[1] )
            error.append([f, found])
    return {'lig' : lig, 'rec': rec, 'flex':flex, 'error': error}        




def simplebasename(name):
    """ WARNING! This works only on POSIX systems
        if a system-dependent mechanism is required, use hf.filetoname)
    """
    if '/' in name:
        name = name.rsplit('/',1)[1]
    name = name.rsplit('.',1)[0]
    return name



def filetoname(filename, stripString=''):
    """ usual string to strip could be '_rigid'
        from a rigid PDBQT receptor file
    
    """
    #print "filetoname>", filename
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    return name.replace(stripString, '')


def xfindLigandsInDlg(dlg_list,  # XXX DISABLED! XXX
                    checkSuccess=True,
                    variable=None,
                    widget=None,
                    handbrake=None,
                    mode='percent'):
    """
    INFO    parses the DLG in dlg_list to identify ligands;
            multi-dlg for the same ligand are collated.

    RETURN  ligands dictionary:
                  ligands[x] = [dlg1,dlg2...]

            list of problematic/unsuccessful dlg files (if found)

    OPTIONS An optional Tk widget and a variable to be updated can be provided.
            Update mode can be 'percent' or 'value'
            handbrake : a global variable that can be checked to halt the process

    """
    if not variable and widget:
        print "requested to update a widget, but None provided (widget,var)"
        doUpdate=False
    ligands = {}
    problematic = []
    c=0
    t=len(dlg_list)
    qs = QuickStop()
    for f in dlg_list:
        if handbrake: return ligands,problematic
        c+=1
        if doUpdate:
            if mode=='percent':
                x=int(percent(c,t))
            elif mode=='value':
                x=c
            variable.set(x)
            widget.update()
        try:
            lines = getLines(f)
            for l in lines:
                if l.startswith("DPF> move"):
                    l = l.split("DPF> move", 1)[1].split(".pdbqt")[0]
                    if checkSuccess and not "Successful" in lines[-5]:
                        raise qs
                    if not l in ligands:
                        ligands[l] = [f]
                    else:
                        ligands[l].append(f)
                    break
        except QuickStop:
            if DEBUG: print "[debug] problem reading file:",f
            problematic.append(f)
    return ligands, problematic


# geometry stuff
def quickdist(f,s,sq = False):
    """ works with coordinates/vectors"""
    d=(f[0]-s[0])**2 + (f[1]-s[1])**2 + (f[2]-s[2])**2
    if sq: return sqrt(d)
    else:  return d

def dist(f, s, sq=False):  
    """ works with PDB(QT) lines"""
    if sq: 
        #print (f[30:38], f[38:46], f[46:54])
        #print (s[30:38], s[38:46], s[46:54])

        return sqrt((float(f[30:38])-float(s[30:38]))**2 +\
                    (float(f[38:46])-float(s[38:46]))**2 +\
                    (float(f[46:54])-float(s[46:54]))**2  )
    else:  return (float(f[30:38])-float(s[30:38]))**2 +\
                  (float(f[38:46])-float(s[38:46]))**2 +\
                  (float(f[46:54])-float(s[46:54]))**2




# graph stuff
def getDistMatrixOLD(data, square=0):


    # generates the NxN distance matrix from data

    #print "DISTMATRIX1"
    #import time
    #t0 = time.time()
    mtx = []
    for i in range(len(data)):
        a1 = data[i]
        row = []
        for j in range(len(data)):
            if not i==j:
                a2 = data[j]
                #print a1, a2
                #row.append(func( a1[1], a2[1])
                # quickdist gives squared dist!
                row.append(quickdist(a1[1], a2[1], sq=square)) # CHANGED Monday, April 23 2012 => problematic 
                #row.append(quickdist(a1, a2, sq=square)) # CHANGED Monday, April 23 2012 => problematic 

                # XXX  File "/entropia/local/rc3/MGLToolsPckgs/AutoDockTools/piStackingAndRingDetection.py", line 399, in findLigandRings
                #row.append( dist(a1, a2, sq=square) ) # XXX WORKING WITHVS
            else:
                row.append(0)
        mtx.append(row)
    #print time.time() - t0
    return mtx


def getDistMatrix(data, square=0):
    # XXX update to use np.array pre-initialized
    #     to save 50% of time skipping calculating b,a
    #     if a,b already calculated
    #print "DISTMATRIX2"
    #import time
    #t0 = time.time()
    mtx = -ones( (len(data), len(data)))
    for i in range(len(data)):
        a1 = data[i]
        for j in range(len(data)):
            a2 = data[j]
            if i == j:
                mtx[i,j] = 0.
            else:
                if not mtx[j,i] == -1:
                    mtx[i,j] =  mtx[j,i]
                else:
                    mtx[i,j] = quickdist(a1[1], a2[1], sq=square)
    #print time.time() - t0
    return mtx


def makeGraph(nodes_list, distance_matrix, cutoff, exclusion_list = []):
    # generates the connection graph in the nodes
    graph = {}
    for i in nodes_list:
        bound = []
        for j in range(len(distance_matrix)):
            if (not j in exclusion_list) and (not i == j):
                if distance_matrix[i][j] < cutoff:
                    bound.append(j)
        graph[i] = bound
    return graph # { i : [ a,b,c...], ... }



# vector stuff # TODO use numpy?


def makeCircleOnPlane(center, r, normal, points = 8):
    """
    Calculate the points of a circle lying on an arbitrary plane
    defined by the normal vector.
    center : coords of center of the circle
    r      : radius
    normal : normal of the plane where the circle lies
    points : number of points for the circle
    
    # http://www.physicsforums.com/showthread.php?t=123168
    # P = Rcos(theta))U + Rsin(theta)N x U +c
    # Where u is a unit vector from the centre of the circle 
    # to any point on the circumference; R is the radius; 
    # n is a unit vector perpendicular to the plane and c is the centre of the circle.

    http://forums.create.msdn.com/forums/p/9551/50048.aspx
    A coworker pointed out a trick to get a vector perpendicular to the normal vector:
    simply swap two of the values, negate one of those, and zero the third.
    So, if I have a normal vector of form Vector3(a, b, c), then one such vector that 
    is perpendicular to it is Vector3(b, -a, 0).  Thus, there are six possible vectors 
    that are attainable by this method.  The only trouble case is when the normal vector 
    contains elements whose values are zero, in which case you have to be a bit careful 
    which values you swap and negate.  You just never want to end up with the zero vector.
    """
    N = normal
    U = array([N[1], -N[0], 0], 'f')
    step = PI2/points
    circle = []
    for i in range(points):
        theta = PI2-(step*i)
        P = (r*cos(theta)*U)+(r*sin(theta))*(cross(N,U))+center
        P = normalize(vector(center,P))*r
        P = vecSum(P,center)
        circle.append(P)
    return circle


def rotatePoint(pt,m,ax):
    """
    Rotate a point applied in m around a pivot ax ?


    pt = point that is rotated
    ax = vector around wich rotation is performed

        ?????? CHANGING THE INPUT VALUE?
    """
    # From Ludo
    # point 
    x=pt[0]
    y=pt[1]
    z=pt[2]

    # rotation pivot
    u=ax[0]
    v=ax[1]
    w=ax[2]
    ux=u*x
    uy=u*y
    uz=u*z
    vx=v*x
    vy=v*y
    vz=v*z
    wx=w*x
    wy=w*y
    wz=w*z
    sa=sin(ax[3])
    ca=cos(ax[3])
    #pt[0]=(u*(ux+vy+wz)+(x*(v*v+w*w)-u*(vy+wz))*ca+(-wy+vz)*sa)+ m[0]
    #pt[1]=(v*(ux+vy+wz)+(y*(u*u+w*w)-v*(ux+wz))*ca+(wx-uz)*sa)+ m[1]
    #pt[2]=(w*(ux+vy+wz)+(z*(u*u+v*v)-w*(ux+vy))*ca+(-vx+uy)*sa)+ m[2]
    p0 =(u*(ux+vy+wz)+(x*(v*v+w*w)-u*(vy+wz))*ca+(-wy+vz)*sa)+ m[0]
    p1=(v*(ux+vy+wz)+(y*(u*u+w*w)-v*(ux+wz))*ca+(wx-uz)*sa)+ m[1]
    p2=(w*(ux+vy+wz)+(z*(u*u+v*v)-w*(ux+vy))*ca+(-vx+uy)*sa)+ m[2]
    #b = [pt, m, ax]

    return array([ p0, p1, p2])


def atomsToVector(at1, at2=None, norm=0):
    at1 = atomCoord(at1)
    if at2: at2 = atomCoord(at2)
    return vector(at1, at2, norm=norm)

def vector(p1 , p2 = None, norm = 0): # TODO use Numpy?
    if not p2 == None:
        vec = array([p2[0]-p1[0],p2[1]-p1[1],p2[2]-p1[2]],'f')
    else:
        vec = array([p1[0], p1[1], p1[2] ], 'f' )

    if norm:
        return normalize(vec)
    else:
        return vec



def norm(A): # TODO use Numpy
        "Return vector norm"
        return sqrt(sum(A*A))

def normalize(A): # TODO use Numpy
        "Normalize the Vector"
        return A/norm(A)

def calcPlane(p1, p2, p3):
    # returns the plane containing the 3 input points
    v12 = vector(p1,p2)
    v13 = vector(p3,p2)
    return normalize(cross(v12, v13))

def dot(vector1, vector2):  # TODO remove and use Numpy
    dot_product = 0.
    for i in range(0, len(vector1)):
        dot_product += (vector1[i] * vector2[i])
    return dot_product

def vecAngle(v1, v2, rad=1): # TODO remove and use Numpy?
    angle = dot(normalize(v1), normalize(v2))
    #print angle, math.degrees(angle)
    try:
        if rad:
            return acos(angle)
        else:
            return degrees(acos(angle))
    except:
        print "#vecAngle> CHECK TrottNormalization"
        return 0

def vecSum(vec1, vec2): # TODO remove and use Numpy # TODO to be used in the PDBQT+ data!
    return array([vec1[0]+vec2[0], vec1[1]+vec2[1], vec1[2]+vec2[2] ], 'f')


def intersect(a,b):
    return list(set(a) & set(b))

def normValue(v, vmin, vmax, normrange=[0,10]):
    # http://mathforum.org/library/drmath/view/60433.html
    # min = A
    # max = B
    # v   = x
    # y = 1 + (x-A)*(10-1)/(B-A)
    #return  1 + (v-vmin)*(10-1)/(vmax-vmin)
    return  normrange[0] + (v-vmin)*( normrange[1] )/(vmax-vmin)
    #top = (v-vmin)(10-1)
    #down = (vmax-vmin)
    #x =  1 + top/down
    #return x

def normProduct(a, b, mode = 'simple'):
    if mode =='simple': return a*b
    elif mode =='scaled': return (a*b)*(a+b)


def avgVector(vec_list, normalize=False):
    # XXX NOT WORKING!!!
    # http://devmaster.net/forums/topic/5443-average-direction-vector/
    #weight = 1;
    #average = vec[0];
    #for (i = 1; i < n; ++i)
    #{
    #    find angle between average and vec[i];
    #    angle *= weight / (weight + 1);
    #    average = rotate vec[i] towards average by angle;
    #    ++weight;
    #}
    print "avgVector> NOT WORKING!!!! NEVER TESTED"

    weight = 1
    average = vec_list[0]
    for i in range(len(vec_list)-1):
        angle = vecAngle(average, vec_list[i+1])
        angle *= weight / (weight+1)
        #average = rotatePoint(pt,m,ax)
        average = rotatePoint(vec_list[i+1],m,ax)
        # XXX m?
        # XXX ax?
        weight += 1
    return average


def coplanar(plane, coord_list = [], reference = [0., 0., 0.], tolerance = 0.2):
    """ return list of coordinates that are within <tolerance> 
        from the plane. If the reference is provided, vectors will be 
        calculated with <reference> as origin.

    """
    coplane_list = []
    for c in coord_list:
        pos = vector(reference, c)
        if dot(plane, pos) <= tolerance:
            coplane_list.append(c)
    return coplane_list


#####################################
######## END VECTOR STUFF ###########
#####################################




def getAtomsFromString(string,mol):
    """ fast selection method for PMV
        string should be something like A:THR276:O
        mol is a PMV molecule instance
    
    """
    try:
        string = string.split(":")
        chain = string[0]
        res = string[1]
        atom = string[2]
        chain = mol.chains.get(chain)
        res = ch.residues.get(res)
        atoms = res.atoms.get(atoms)
    except:
        print "getAtomsFromString> ERROR: something went wrong with ['%s']" % string
        return False
    return atoms[0]



def timerFunction(func,*arg):
    t1=time.time()
    res = apply(func,(arg))
    print time.time()-t1 
    return res


#####################
# VALIDATORS

def validateEmail(string, localhost=False, exclude='', allowempty=0):
    """validate a string to be a valid email

        it is possible to specify if 'localhost' is accepted
        or a value that is not acceptable (i.e. 
        an example like 'user@domain.edu')
    """

    string = str(string)
    #print string, string.split('.')
    if string.strip() == "":
        if allowempty:
            return True
        return False
    if "@" in string:
        try:
            name,domain = string.split("@")
            if (not localhost) and (not "." in string):
                return False
            else:
                splitted = string.split('.')
                for s in splitted:
                    if not s.strip():
                        return False
            return True
        except:
            return False
    return False


def validatePosInt(value, nozero=True):
    if value == '':
        return Pmw.PARTIAL
    for a in value:
        if not a.isdigit():
            return Pmw.ERROR
    try:
        if nozero:
            if int(value) <= 0:
                return Pmw.ERROR
        else:
            if int(value) < 0:
                return Pmw.ERROR
    except:
        return Pmw.ERROR
    return Pmw.OK


def validatePosNonNullInt(value):
    return validatePosInt(value, nozero=True)

def validateFloat(value, positive=False):
    if value == '':
        return Pmw.PARTIAL
    try:
        float(value)
        if positive and not float(value) > 0:
            return Pmw.ERROR
        return Pmw.OK
    except:
        return Pmw.ERROR
        

def validateFloatPos(value):
    return validateFloat(value, positive=True)

def validateAscii(value, allowempty=False):
    """ validate string as ASCII """
    valid_chars = "-_.+(),%s%s" % (string.ascii_letters, string.digits)
    value == value.strip()
    if value == '':
        if allowempty:
            return Pmw.OK
        else:
            return Pmw.PARTIAL
    for a in value:
        if not a in valid_chars:
            return Pmw.ERROR
    return Pmw.OK


def validateAsciiEmpty(value):
    """ validate string as ASCII or empty"""
    return validateAscii(value, allowempty=True)


def validateInternetHost(value, allowempty=0):
    # ValidHostnameRegex = "^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$";
    ValidHostnameRegex = "^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$";


def validateHostname(hostname):
    """ provide a Pmw-compliant validation"""
    valid_chars = "._-%s%s" % (string.ascii_letters, string.digits)
    if hostname == '':           # empty
        return Pmw.PARTIAL
    for c in hostname:           
        if not c in valid_chars: # not allowed chars
            return Pmw.ERROR
    return Pmw.OK



def validateWebLink(string, localhost=False, forcehttp=True):
    """ validate a web link """
    string=str(string).strip()
    #print "STRING IS |%s|"% string
    if forcehttp:
        if not string.startswith('http://') and not string.startswith('https://'):
            print "MISSING HTTP!!!"
            return False
    return True

def validateFname(string, posix=False):
    """ """
    valid = _allowedfilenamechars()
    if posix:
        valid += '/' + '~'
    if string.strip() == '':
        return Pmw.PARTIAL
    for s in string:
        if not s in valid:
            return Pmw.ERROR
    return Pmw.OK


def validateUnixPath(string):
    return validateFname(string, posix=True)

def _allowedfilenamechars(is_path=False, posix=True):
    """provide basic set of chars that can be used to save files
    on pretty much all architectures (kinda)
    """
    a = "-_.+,%s%s" % (string.ascii_letters, string.digits)
    if is_path:
        if posix:
            a += '/' + '~'
        else:
            a += '\\', '%'
    return a

def validFilename(string, lower=False):
    """return a string that can be used as a valid file(dir) name in most
        OS's... kinda...
    """
    if lower:
        return "".join([ x for x in string if x in _allowedfilenamechars()]).lower()
    return "".join([ x for x in string if x in _allowedfilenamechars()])

def validPath(string, lower=False, posix=True):
    if lower:
        return "".join([ x for x in string if x in _allowedfilenamechars(is_path=True, posix=posix)]).lower()
    return "".join([ x for x in string if x in _allowedfilenamechars(is_path=True, posix=posix)])



#  / validators
##################

###################### GUI
#
#
#from Tkinter import *

class PercentPie(Canvas):
    """ Draws a percent pie configurable and modifiable.
        Example:    
            root = Tk()
            pie_1 = PercentPie(root, radius = 60)
            pie_1.pack()
            pie_1.set_percent(35)
    """
    #def __init__(self, master, radius = 75, h = 100, w = 100, center = [0,0], pad = 3,
    def __init__(self, master, radius = 75, pad = 3, border = 'black', fill = 'red', shadow=True):
        # TODO add the coloring options (as RGB)
        Canvas.__init__(self,master)
        self.frame = Frame(self)
        self.DEBUG = False
        center = [0,0]
        if shadow:
            extra=4
        else:
            extra=2
        w=pad+extra+radius
        h=pad+extra+radius

        #print 'R:%d, %dx%d' % (radius, w,h)
        self.canvas = Canvas(self.frame, width = w, height = h)
        # shadow
        if shadow:
            self.shadow = self.canvas.create_oval(center[0]+pad-1,
                                              center[1]+pad-1, 
                                              center[0]+pad+3+radius, 
                                              center[1]+pad+3+radius, 
                                              fill = 'gray65', # COLOR HERE
                                              outline = 'gray65') 
        # CIRCLE base and dark boundary
        self.bg = self.canvas.create_oval(center[0]+pad-1,
                                          center[1]+pad-1, 
                                          center[0]+pad+1+radius, 
                                          center[1]+pad+1+radius, 
                                          fill = 'red', # COLOR HERE
                                          outline = 'black') 
        # CIRCLE halo color transition
        self.bg = self.canvas.create_oval(center[0]+pad, 
                                          center[1]+pad, 
                                          center[0]+pad+radius, 
                                          center[1]+pad+radius, 
                                          outline = 'DarkSalmon') # COLOR HERE
        # CIRCLE pie filler
        self.arc = self.canvas.create_arc(center[0]+pad,
                                          center[1]+pad,
                                          center[0]+pad+radius, 
                                          center[1]+pad+radius,
                                          start = 0, extent = 0,
                                          fill = 'red', outline = 'red')# COLOR HERE
                                          #tags = name)  # TODO is name necessary?
        # TEXT shadow
        self.text_shadow = self.canvas.create_text(center[0]-1+pad+radius/1.8,
                                                   center[1]+1+pad+radius/2, 
                                                   font = 'helvetica 9 bold', 
                                                   #fill = 'steel blue',  # COLOR HERE
                                                   fill = 'black',  # COLOR HERE
                                                   text = ( "000.000%") )
        # TEXT main
        self.text = self.canvas.create_text(center[0]+pad+radius/1.8,
                                            center[1]+pad+radius/2,
                                            font = 'helvetica 9 bold', 
                                            fill = 'white',  # COLOR HERE
                                            text = ( "000.000%") ) 
        self.frame.grid(row = 0, column = 0, sticky = N+W+E+S)
        self.canvas.grid(row = 0, column = 0, sticky = N+W+E+S)
    def set_percent(self, percent):
        if percent == 0.00:
            if self.DEBUG: print "PercentPie> got a ZERO percent"
            self.canvas.itemconfig(self.arc, start = 0, 
                                    extent = 0, 
                                    fill = 'red', outline = 'red') # COLOR HERE
        else:
            if self.DEBUG: print "PercentPie> got a non-ZERO percent,"
            if percent == 100:
                if self.DEBUG: print "100!"
                angle = 359.9
                start = -0.1
                self.canvas.itemconfig(self.arc, start = start, 
                                        extent = angle, 
                                        fill = 'SteelBlue1', outline = 'SteelBlue2') # COLOR HERE
            else:
                if self.DEBUG: print percent
                angle = (float(percent)/float(100))*float(360)
                start = -angle/2.
                self.canvas.itemconfig(self.arc, start = start, extent = angle, 
                                        fill = 'SteelBlue1', outline = 'steel blue') # COLOR HERE
            if self.DEBUG:
                print "\n\n\n\n\nPercentPie> the arc" ,self.arc, "\n\n\n\n\n"
                print "CONFIGURE ME!"
                for i in self.canvas.itemconfig(self.arc):
                    print i, "=", self.canvas.itemconfig(self.arc, i)
                print "\n\n\n\n\nPercentPie> the arc" ,self.arc, "\n\n\n\n\n"
        self.canvas.itemconfig(self.text, text = ( ("%3.3f %s") % ( percent, "%") )) 
        self.canvas.itemconfig(self.text_shadow, text = ( ("%3.3f %s") % ( percent, "%") )) 




class ProgressBar(Canvas):
    def __init__(self, master, variable=None, w=200, h=20, font_size=10,
                manager='pack', extraShadow=True):
        Canvas.__init__(self,master)
        self.frame = Frame(self)
        self.canvas=Canvas(self.frame, width=w+2, height=h+2)
        self.value=0
        self.width=w
        self.height=h
        self.start=(1,1)
        self.end=(w,h)
        if not variable == None:
            self.percent = variable
        else:
            self.percent = DoubleVar(value=0.0)
        self.PercentTracer=self.percent.trace_variable('w', self.set_percent)
        #buff_x=5
        #buff_y=10

        self.TEXT=[]
        shadow = True
        font_family = "helvetica"
        font_style  = 'bold'
        text_color = 'white'
        shadow_color='black'
        shadow_color='#00164e'

        self.font=font_family+" "+str(font_size)+" "+font_style

        # base color
        self.base = self.canvas.create_rectangle(self.start,self.end,fill='#cccccc',outline='')

        # progressing bar
        self.bar = self.canvas.create_rectangle(self.start,0,self.height,fill='#0080ff',outline='#0069d4',width=2)

        # lines
        #self.bar = self.canvas.create_line(width-98,1,width-98,height,width=2,fill='#bbddff')

        # shadow text
        tx = (w/2)# +(w/20)
        ty = (h/2)+(h/15)
        t1 = self.canvas.create_text(tx-1, ty+0, font=self.font, fill = shadow_color, text="0%")
        t2 = self.canvas.create_text(tx+1, ty+0, font=self.font, fill = shadow_color, text="0%")
        t3 = self.canvas.create_text(tx+0, ty+1, font=self.font, fill = shadow_color, text="0%")
        t4 = self.canvas.create_text(tx+0, ty-1, font=self.font, fill = shadow_color, text="0%")
        self.TEXT.append(t1)
        self.TEXT.append(t2)
        self.TEXT.append(t3)
        self.TEXT.append(t4)

        if extraShadow:
            t4b = self.canvas.create_text(tx+1, ty+1, font=self.font, fill = 'black', text="0%")
            self.TEXT.append(t4b)
            

        # text
        t5 = self.canvas.create_text(tx, ty, font=self.font, fill = text_color, text="0%")
        self.TEXT.append(t5)

        # frame outline
        self.canvas.create_rectangle(self.start, self.end,fill='',outline='black')
        if manager=='pack':
            self.canvas.pack(expand=Y,fill=BOTH,anchor=CENTER, side='top')
            self.frame.pack(expand=Y,fill=BOTH,anchor=CENTER, side='top')
        elif manager =='grid':
            self.canvas.grid(row=0,column=0,sticky=W+E)
            self.frame.grid_columnconfigure(0, weight=10)
            self.frame.grid_rowconfigure(0, weight=10)
            self.frame.grid(row=0,column=0)


    def set(self, value):
        """ internal method used to set the variable value
            this is used to avoid the error

            RuntimeError: main thread is not in main loop

            when using threads
        """
        self.percent.set(value)

    def pc(self, value,width):
        r = (width*value)/100
        #r = (v/t)*100
        if r<1 : return 1
        return r

    def hide_text(self):
        for t in self.TEXT:
            self.canvas.itemconfig(t, text='')

    def disable(self):
        self.hide_text()
        self.canvas.itemconfig(self.base, fill='')
        
    def set_text(self, msg):
        for t in self.TEXT:
            self.canvas.itemconfig(t, text=msg)

    def set_percent(self,name, index, mode):
        v = self.pc(self.percent.get(),self.width)
        msg = ("%d%%" % self.percent.get())
        # update text
        self.set_text(msg)
        # update bar
        self.canvas.coords(self.bar, self.start[0], self.start[1], v ,self.height)



class ProgressBarThreadsafe(Frame):
    def __init__(self, master, w=200, h=20, font_size=10,
                manager='pack', extraShadow=True):
        #Canvas.__init__(self,master, width=w+2, height=h+2)
        self.BORDER = { 'bd':1,'highlightbackground':'black',
            'borderwidth':2,'highlightcolor':'black','highlightthickness':1}

        Frame.__init__(self,master, bg='white') # , relief = 'sunken', **self.BORDER )
        self.frame = self
        self.canvas=Canvas(self.frame, width=w+2, height=h+2, bg='white')
        self.value=0
        self.width=w
        self.height=h
        self.start=(1,1)
        self.end=(w,h)
        self.percent = 0
        self.percent = 0.0
        #buff_x=5
        #buff_y=10

        self.TEXT=[]
        shadow = True
        font_family = "helvetica"
        font_style  = 'bold'
        text_color = 'white'
        shadow_color='black'
        shadow_color='#00164e'

        self.font=font_family+" "+str(font_size)+" "+font_style

        # base color
        self.base = self.canvas.create_rectangle(self.start,self.end,fill='#cccccc',outline='')

        # progressing bar
        self.bar = self.canvas.create_rectangle(self.start,0,self.height,fill='#0080ff',outline='#0069d4',width=2)

        # lines
        #self.bar = self.canvas.create_line(width-98,1,width-98,height,width=2,fill='#bbddff')

        # shadow text
        tx = (w/2)# +(w/20)
        ty = (h/2)+(h/15)
        t1 = self.canvas.create_text(tx-1, ty+0, font=self.font, fill = shadow_color, text="0%")
        t2 = self.canvas.create_text(tx+1, ty+0, font=self.font, fill = shadow_color, text="0%")
        t3 = self.canvas.create_text(tx+0, ty+1, font=self.font, fill = shadow_color, text="0%")
        t4 = self.canvas.create_text(tx+0, ty-1, font=self.font, fill = shadow_color, text="0%")
        self.TEXT.append(t1)
        self.TEXT.append(t2)
        self.TEXT.append(t3)
        self.TEXT.append(t4)

        if extraShadow:
            t4b = self.canvas.create_text(tx+1, ty+1, font=self.font, fill = 'black', text="0%")
            self.TEXT.append(t4b)
            

        # text
        t5 = self.canvas.create_text(tx, ty, font=self.font, fill = text_color, text="0%")
        self.TEXT.append(t5)

        # frame outline
        self.canvas.create_rectangle(self.start, self.end,fill='',outline='black')
        if manager=='pack':
            self.canvas.pack(expand=Y,fill=BOTH,anchor=CENTER, side='top')
            self.frame.pack(expand=Y,fill=BOTH,anchor=CENTER, side='top')
        elif manager =='grid':
            self.canvas.grid(row=0,column=0,sticky=W+E)
            self.frame.grid_columnconfigure(0, weight=10)
            self.frame.grid_rowconfigure(0, weight=10)
            self.frame.grid(row=0,column=0)


        """ internal method used to set the variable value
            this is used to avoid the error

            RuntimeError: main thread is not in main loop

            when using threads
        """

    def pc(self, value, width):
        r = (width*value)/100
        #r = (v/t)*100
        if r<1 : return 1
        return r

    def hide_text(self):
        for t in self.TEXT:
            self.canvas.itemconfig(t, text='')

    def disable(self):
        self.hide_text()
        self.canvas.itemconfig(self.base, fill='')
        
    def set_text(self, msg):
        for t in self.TEXT:
            self.canvas.itemconfig(t, text=msg)

    def set(self, value):
        self.percent = value
        v = self.pc(self.percent,self.width)
        msg = ("%d%%" % int(self.percent) )
        # update text
        self.set_text(msg)
        # update bar
        self.canvas.coords(self.bar, self.start[0], self.start[1], v ,self.height)









def hex2rgb(string, base = 1, pmv = True):
    """
    convert hex color value to rgb base 1 or 255
       -TkInter works in HEX or RGB_255
       -PMV works with RGB_1

    'string' looks like '#00ff00'
    """
    r = int(string[1:3], 16)
    g = int(string[3:5], 16)
    b = int(string[5:7], 16)
    if base == 1:
        r = float(r)/255.
        g = float(g)/255.
        b = float(b)/255.
        if not pmv: return array( [r,g,b], 'f' )
        else: return (r,g,b)
    if base == 255: return array( [ r, g, b ], 'f')




def TkSeparator(parent,row,col,height=2, width=1,columnspan=3, rowspan=1):
    separator = Frame(parent,height=height,width=width,bd=1,relief=SUNKEN)
    separator.grid(row = row,
                   column=col,
                   sticky=E+W,
                   columnspan=columnspan,
                   rowspan=rowspan,
                   padx=2,
                   pady=5)
    return separator




class TextCopyPaste(Text):
    # http://mail.python.org/pipermail/tutor/2004-July/030398.html
    def __init__(self, master, **kw):
        Text.__init__(self, master, **kw)
        self.bind('<Control-c>', self.copy)
        self.bind('<Control-x>', self.cut)
        self.bind('<Control-v>', self.paste)
        
    def copy(self, event=None):
        self.clipboard_clear()
        try:
            text = self.get("sel.first", "sel.last")
            #print "GETTING SELECTION"
            #self.clipboard_append(text)
        except: 
            text = self.get(1.0, END)
            #print "GETTING ALL"
        if len(text): 
            self.clipboard_append(text)

    def cut(self, event=None):
        try:
            self.copy()
            self.delete("sel.first", "sel.last")
        except:
            pass

    def paste(self, event=None):
        try:
            text = self.selection_get(selection='CLIPBOARD')
            self.insert('insert', text) 
        except: pass

    def nuke(self, event=None):
        self.delete(1.0, END) 



def userInputDir(parent, title='Select a directory', initialdir=None, createnew=1):
    import tkFileDialog as tkf
    import tkMessageBox as tkm
    import os
    title = 'Select the directory where to store result files'
    outdir = tkf.askdirectory(parent=parent, title=title,
        initialdir=initialdir)
    if not len(outdir):
        return
    if not os.path.exists(outdir):
        title = "New directory"
        msg = "The directory doesn't exist.\n\nDo you want to create it?"
        if tkm.askyesno(title, msg, parent=parent, icon=tkm.INFO):
            try:
                os.makedirs(outdir, 0755)
            except:
                err = sys.exc_info()[1]
                title = "Error creating directory"
                msg = ("An error occurred while creating "
                       "the new directory:\n\n"
                       "DIRECTORY:\t'%s'\n"
                       "ERROR:\t%s\n\n"
                       "Operation aborted."
                       ) % (outdir, err)
                tkm.showerror(title, msg, parent=parent)
                return    
    return outdir


import Tkinter as tk
import tkFont
class SimpleTable:
    """ simple N x M table in Tk"""
    def __init__(self, parent, data=[], 
            title_item = 'row', # row, column, both, None? XXX
            title_color = '#d8daf8',
            cell_color = 'white',
            title_font = None,
            cell_font = None,
            cell_width = 30,
            title_width= None,
            autowidth = False,
            debug = False,
            fullprecision = False,
            title_justify='center', # tk label anchor values
            cell_justify='center',  #  tk label anchor values
            #expand=1,
            #fill='both',
            #padx = 0, pady=0
            ):

        self.debug = debug
        self.parent = parent
        self.data = data
        self.title_item = title_item
        self.autowidth = autowidth
        self.title_color = title_color
        self.title_font = title_font
        self.title_width = title_width
        self.title_justify = title_justify

        self.cell_color = cell_color
        self.cell_width = cell_width
        self.cell_font = cell_font
        self.cell_justify = cell_justify
        self.cells = []
        self.frame = None
        self.fullprecision = fullprecision


        #self.packing_conf = { 'expand' : expand, 'fill' : fill, 'padx':padx, 'pady':pady}

        if len(self.data):
            self._build()


    def _build(self):
        
        if self.autowidth:
            width = 0
            maxlongw = 0
            for x in self.data:
                for y in x:
                    longestword = max(str(y).split("\n"), key=len)
                    width = max(width, len(longestword))

            self.cell_width = width+2
            if self.title_width == None:
                self.title_width = self.cell_width
        self.frame = tk.Frame(self.parent, bd=1, relief='solid')
        f = self.frame
        vbar = tk.Frame(f,height=10,width=2,bd=1,relief='sunken') # grid(row=r,column=c+1,rowspan=1,sticky='ns')
        hbar = tk.Frame(f,height=2,width=10,bd=1,relief='sunken') # grid(row=r+1,column=c,columnspan=4,sticky='we')

        default = {}
        for x in range(len(self.data)):
            row = []
            for y in range(len(self.data[x])):
                val = self.data[x][y]
                if isinstance(val, float):
                    if not self.fullprecision:
                        val = '%2.3f' % val
                if (self.title_item in ['row', 'both'] and x == 0) or (self.title_item in ['column', 'both'] and y == 0):
                    # title color
                    color = self.title_color
                    # title font
                    if isinstance(self.title_font, tkFont.Font):
                        font = self.title_font
                    # title size
                    if not self.title_width == None:
                        width = self.title_width
                    else: 
                        width = self.cell_width
                    relief = 'ridge'
                    justify = self.title_justify
                else:
                    # cell color 
                    color = self.cell_color
                    # cell font
                    if isinstance(self.cell_font, tkFont.Font):
                        font = self.cell_font
                    # cell width
                    width = self.cell_width
                    justify = self.cell_justify
                    #
                    relief = 'ridge'

                default['bg'] = color
                default['font'] = font
                default['width'] = width
                default['relief'] = relief
                default['anchor'] = justify

                # cell
                c = tk.Label(f, text=val, **default)
                c.grid(row=x*2, column=y*2, sticky='nsew')
                row.append(c)
                # v spacer
                if self.debug: 
                    print "%d:%d" % (y, len(self.data[x])),
                ## if not y == len(self.data[x])-1:
                ##     vbar = tk.Frame(f,height=10,width=2,bd=1,relief='sunken') # grid(row=r,column=c+1,rowspan=1,sticky='ns')
                ##     vbar.grid(row=x*2, column = (y*2)+1, sticky='ns',rowspan=1)
            self.cells.append(row)

            if self.debug: print " "
            # h spacer
            if not x == len(self.data)-1:
                relief = 'sunken'
                height = 2
            else:
                relief = 'solid'
                height = 1

            ## hbar = tk.Frame(f,height=height,width=10,bd=1,relief=relief) # grid(row=r+1,column=c,columnspan=4,sticky='we')
            ## hbar.grid(row=x*2+1, column = 0, sticky='we', columnspan = len(self.data[0])*2 )


        ## vbar2 = tk.Frame(f,height=10,width=1,bd=1,relief='solid') # grid(row=r,column=c+1,rowspan=1,sticky='ns')
        ## vbar2.grid(row=0, column = (y*2)+1, sticky='ns',rowspan=len(self.data)*2)

                
    def setData(self, data):
        if not self.frame == None:
            self.frame.pack_forget()
        self.data = data
        self._build()
        self.frame.pack(expand=0, fill=None ) # **self.packing_conf)

        



class DoubleSlider(tk.Frame):

    def __init__(self, parent, best, worst, width=15, resolution=0.01, orient='horizontal'):

        tk.Frame.__init__(self, parent)
        slenght=7
        self.best = best
        self.worst = worst
        f = tk.Frame(self)
        # label
        tk.Label(f, text='best',width=5,anchor='e').pack(expand=0,fill='none', anchor='s', side='left')
        # scale
        self.bestscale = tk.Scale(f, from_=self.best, to=self.worst, orient=orient, troughcolor='#00ff03',
                resolution=resolution, showvalue=False, sliderlength=slenght, width=width)
        self.bestscale.pack(expand=0,fill='x',anchor='s', side='left')
        # entry
        self.bestentry = Pmw.EntryField(f, entry_width=8, validate = {'validator':'real', 'minstrict':0},
            entry_justify='right', errorbackground='pink', command=self.setbest)
        self.bestentry.pack(expand=0,fill='none', anchor='s', side='left')
        f.pack(expand=0,anchor='n', side='top')

        f = tk.Frame(self)
        # label
        tk.Label(f, text='worst',width=5,anchor='e').pack(expand=0,fill='none', anchor='w', side='left')
        # scale
        self.worstscale = tk.Scale(f, from_=self.best, to=self.worst, orient=orient,troughcolor='#FF6300', 
                resolution=resolution, showvalue=False, sliderlength=slenght, width=width)
        self.worstscale.pack(expand=0,fill='x',anchor='w', side='left')
        # entry
        self.worstentry = Pmw.EntryField(f, entry_width=8, validate = {'validator':'real', 'minstrict':0}, 
            entry_justify='right', command=self.setworst)
        self.worstentry.pack(expand=0,fill='none', anchor='w', side='left')
        f.pack(expand=0,anchor='n', side='top')

        self.bestscale.config(command=self.callbackBest)
        self.worstscale.config(command=self.callbackWorst)

    def callbackBest(self, event=None):
        event = float(event)
        
        right = math.fabs(event - self.best)
        left = math.fabs(self.worstscale.get() - self.best)

        if right < left:
            self.worstscale.set(event)
        self.bestentry.setvalue(event)

    def callbackWorst(self, event=None):
        """ """
        event = float(event)
        right = math.fabs(self.bestscale.get() - self.best)
        left = math.fabs(self.worstscale.get() - self.best)
        if right < left:
            self.bestscale.set(event)
        self.worstentry.setvalue(event)


    def setbest(self, value=None):
        """ """
        if value == None:
            value = float(self.bestentry.getvalue())
        self.bestscale.set(value)

    def setworst(self,value=None):
        """ """
        if value == None:
            value = float(self.worstentry.getvalue())
        self.worstscale.set(value)


    def setmaxmin(self, _max=None, _min=None):
        if _max == None and _min == None:
            return
        from_
        to
        

##### OS SECTION

def getOsInfo():
    #architecture, exec_format = platform.architecture()
    #hostname = platform.node()
    #release = platform.release() # vista, '2.6.32-bpo.5-amd64'
    #system = platform.system()
    return {'architecture': platform.architecture()[0],
            'hostname': platform.node(),
            'release':  platform.release(),
            'system' : platform.system(),
            }



def detectCPUs():
    """
    Detects the number of CPUs on a system. Cribbed from pp.
    http://codeliberates.blogspot.com/2008/05/detecting-cpuscores-in-python.html
    http://www.artima.com/weblogs/viewpost.jsp?thread=230001

    overrided by "import multiprocessor; multuprocessor.cpu_count()" ???
    """
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
            # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else: # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # Windows:
    if os.environ.has_key("NUMBER_OF_PROCESSORS"):
            ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
            if ncpus > 0:
                return ncpus
    return 1 # Default



def cliOpts( cli_arguments, options):
    # options, var = getopt.getopt(argv[1:], 'c:l:f:')
    # cli_arguments = argv[1:]
    # options = 'c:l:f:'
    # XXX incomplete XXX
    opts = {}
    try:
        options, extra = getopt.getopt(cli_arguments, options)
        for o,a in options:
            opts[o] = a
        return opts
    except getopt.GetoptError, err:
        return str(err)


def checkDiskSpace(path, human=False, percent=False):
    # rewrite!
    from platform import uname
    from sys import exc_info
    system_info = uname()
    platform = system_info[0]
    if platform == 'Windows':
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        format_path = (u'%s\\') % path
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(format_path), None, None, ctypes.pointer(free_bytes))
        available = free_bytes.value
        try:
            available = float(available)
        except:
            print "checkDiskSpace[%s]: ERROR => [%s]" % (platform, exc_info()[1])
            available = -1
    elif platform == "Linux" or platform == "Darwin":
        disk = os.statvfs(path)
        capacity = disk.f_bsize * disk.f_blocks
        available = disk.f_bsize * disk.f_bavail
        used = disk.f_bsize * (disk.f_blocks - disk.f_bavail)
    else:
        print "checkDiskSpace[%s]: ERROR unrecognized platform '%s'" % platform
        return -1

    if not human:
        return available
    else:
        factor = [ 1024, 1048576, # mb
                    1073741824, # gb
                    1099511627776, # tb
                  ]
        suffix = [ 'Kb', 'Mb', 'Gb', 'Tb' ]
        
        text = "-1 Kb"
        for i in range(len(factor)):
            fac = factor[i]
            suf = suffix[i]
            curr = available/float(fac)
            if curr < 1:
                try:
                    fac = factor[i-1]
                    suf = suffix[i-1]
                    curr = available/float(factor[i-1])
                except:
                    pass
                    #print "%s" % exc_info()[1]
                break
        text = "%2.3f %s" % (curr, suf)
        #print "checkDiskSpace>", text
        return text     





#### / OS SECTION



################################33

#### PYTHON HELPERS 

def deepCopy(self, item):
    """ perform a deep copy of """
    pass




def TODO():
    if widget:
        # update widget here (percentage of progress bar?)
        text='Importing [%s]' % name
        widget.update(msg=text,progress=pc(t,c))




