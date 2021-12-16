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
#!/usr/bin/env python
from numpy import *
import HelperFunctionsN3P as hf

try:
    DEBUG
except:
    DEBUG = False

COVALENT_BOND_DIST = 1.45
COVALENT_BOND_DIST = COVALENT_BOND_DIST **2 # speed up

def getAromaticRes(receptor):
    # TODO add acids and amides?
    aromatic_res = { "PHE": ["A"],
                 "TYR": ["A"],
                 "HIS": ["A", "N", "NA"],
                 "TRP": ["A", "N", "NA"],
                 "ARG": ["N", "C" , "NA"],
                 "DA" : ["A", "NA", "N"],  # DNA
                 "DC" : ["A", "N", "NA"],
                 "DT" : ["A", "N", "NA"],
                 "DG" : ["A", "N", "NA"],                 
                 "A" : ["A", "NA", "N"],   # DNA/RNA
                 "C" : ["A", "N", "NA"],
                 "G" : ["A", "N", "NA"],                 
                 "T" : ["A", "N", "NA"],
                 "U" : ["A", "N", "NA"],
                 }
    residues = {}
    special = [] # must be treated as a ligand part
    for a in receptor:
        a = a.strip()
        rtype = a[16:21].strip().upper() # NOTE: we can recognize only all caps!
        if a.startswith("HETATM"):
            special.append(a)
        elif a.startswith('ATOM') and rtype in aromatic_res.keys():
            if hf.getAtype(a) in aromatic_res[rtype]:
                res_id = hf.pmvAtomStrip(a).rsplit(":",1)[0] # A:GLY48:N -> A:GLY48
                if not res_id in residues.keys():
                    residues[res_id] = []
                residues[res_id].append(a)
    if special and DEBUG:
        print "found potential co-factor: %d"  % len(special)
        for a in special: print a
    return residues, special # residues = { "A:GLY48" : [ atom, atom, atom..]}

def atomsToVec(atoms):
    a1 = hf.atomCoord(atoms[1])
    a2 = hf.atomCoord(atoms[2])
    a3 = hf.atomCoord(atoms[3])
    centroid = hf.avgCoord(atoms)
    pvector = hf.calcPlane(a1, a2, a3)
    v1 = hf.vector(centroid, a1)
    v2 = hf.vector(centroid, a2)
    normal1 = hf.normalize(cross(v1 ,v2))
    normal2 = hf.normalize(cross(v2 ,v1))
    centroid_norm1 = hf.normalize(hf.vector(centroid, normal1))
    centroid_norm2 = hf.normalize(hf.vector(centroid, normal2))
    return {"centroid":centroid,"plane":hf.normalize(pvector),"normal":[normal1, normal2],\
                        'cnormal' : [centroid_norm1, centroid_norm2]}



#def atomsToVec(atoms):
#    # TODO identify if something is usless (centroid/normal,cnormal)
#    a1 = atomCoord(atoms[1])
#    a2 = atomCoord(atoms[2])
#    a3 = atomCoord(atoms[3])
#    centroid = avgCoord(atoms)
#    pvector = calcPlane(a1, a2, a3)
#    v1 = vector(centroid, a1)
#    v2 = vector(centroid, a2)
#    normal1 = normalize(cross(v1 ,v2))
#    normal2 = normalize(cross(v2 ,v1))
#    centroid_norm1 = normalize(vector(centroid, normal1))
#    centroid_norm2 = normalize(vector(centroid, normal2))
#    return {"centroid":centroid,"plane":normalize(pvector),"normal":[normal1, normal2],\
#                        'cnormal' : [centroid_norm1, centroid_norm2]}






def getResAromaticVectors(residues):
    """
    transform PDBQT residues in centroid,plane data

    INPUT:  residues = { "A:GLY48" : [ atom, atom, atom..], ...}
    OUTPUT: residues = { "A:GLY48" : { centroid_a, centroid_v, plane{, ... }
    """
    for res in residues.keys():
        rtype = res.split(":")[1][0:3] # A:GLY48 => GLY
        try:
            if rtype == "PHE" or rtype == "TYR":
                if len(residues[res]) == 6:
                    pass
                else:
                    if DEBUG: print "Warning! Ignoring residue [ %s ] (missing atoms)" % res
            elif rtype == "TRP":
                if len(residues[res]) >= 9:
                    residues[res] = purgeTrp(residues[res])
                else:
                    if DEBUG: print "Warning! Ignoring residue [ %s ] (missing atoms)" % res
            elif rtype == "HIS":
                if len(residues[res]) >= 5:
                    residues[res] = purgeHis(residues[res])
                else:
                    if DEBUG: print "Warning! Ignoring residue [ %s ] (missing atoms)" % res
            elif rtype == "ARG":
                residues[res] = purgeArg(residues[res])
                if not residues[res] and DEBUG: print "Warning! Ignoring residue [ %s ] (missing atoms)" % res
            elif rtype == "DA" or rtype == "A":
                if len(residues[res]) >= 10:
                    residues[res] = purgeAdenine(residues[res])
                else:
                    if DEBUG: print "Warning! Ignoring residue [ %s ] (missing atoms)" % res
            elif rtype == "DC" or rtype == "C":
                if len(residues[res]) >= 6:
                    residues[res] = purgeAdenine(residues[res])
                else:
                    if DEBUG: print "Warning! Ignoring residue [ %s ] (missing atoms)" % res
            elif rtype == "DG" or rtype == "G":
                if len(residues[res]) >= 10:
                    residues[res] = purgeAdenine(residues[res])
                else:
                    if DEBUG: print "Warning! Ignoring residue [ %s ] (missing atoms)" % res
            if residues[res]:
                residues[res] = atomsToVec(residues[res])
            else:
                del residues[res]
        except:
            if DEBUG: print "Fatal error  in processing residue [ %s ]"% res
            del residues[res]
    return residues

def purgeTrp(atoms):
    """try to purge atoms that are not in the ring(s)"""
    for a in atoms:
        found = False
        if getAtype(a) == "N":
            for c in atoms:
                if not c == a and dist(c,a) < COVALENT_BOND_DIST:
                    found = True
            if not found:
                atoms.remove(a)
                return atoms
    if DEBUG: print "Warning! Residue %s appears to be incomplete" % (atoms[0][17:20]+atoms[0][22:26]+atoms[0][21])
    return False

def purgeHis(atoms):
    """try to purge atoms that are not in the ring(s)"""
    for a in atoms:
        if getAtype(a) == "N" or getAtype(a) == "NA":
            found = 0
            for c in atoms:
                if not c == a and dist(c,a) < COVALENT_BOND_DIST:
                    found = 1
                    break
            if not found:
                atoms.remove(a)
                return atoms
    if DEBUG: print "Warning! Residue %s appears to be incomplete" % (atoms[0][17:20]+atoms[0][22:26]+atoms[0][21])
    return False

def purgeArg(atoms):
    for a in atoms:
        if getAtype(a) == "C":
            candidate = [ a ]
            for n in atoms:
                if not n == a and (getAtype(n) == "N" or getAtype(n) == "NA" ) :
                    if dist(n,a) < COVALENT_BOND_DIST:
                        candidate.append(n)
            if len(candidate) == 4:
                return candidate
    if DEBUG: print "Warning! Residue %s appears to be incomplete" % (atoms[0][17:20]+atoms[0][22:26]+atoms[0][21])
    return False


def purgeAdenine(atoms):
    # look for the single out-of-ring amino nitrogen
    # delete it and return the cleaned up plane
    for a in atoms:
        if getAtype(a) == "N":
            found = 0
            for c in atoms:
                if not c == a and dist(c,a) < COVALENT_BOND_DIST:
                    found += 1
            if not found == 2:
                atoms.remove(a)
                return atoms
    if DEBUG: print "Warning! Residue %s appears to be incomplete" % (atoms[0][17:20]+atoms[0][22:26]+atoms[0][21])
    return False

def purgeCytosine(atoms):
    # look for the single out-of-ring amino nitrogen
    # delete it and return the cleaned up plane
    for a in atoms:
        if getAtype(a) == "N":
            found = 0
            for c in atoms:
                if not c == a and dist(c,a) < COVALENT_BOND_DIST:
                    found += 1
            if not found == 2:
                atoms.remove(a)
                return atoms
    if DEBUG: print "Warning! Residue %s appears to be incomplete" % (atoms[0][17:20]+atoms[0][22:26]+atoms[0][21])
    return False

def purgeGuanine(atom):
    # look for the single out-of-ring amino nitrogen
    # delete it and return the cleaned up plane
    for a in atoms:
        if getAtype(a) == "N":
            found = 0
            for c in atoms:
                if not c == a and dist(c,a) < COVALENT_BOND_DIST:
                    found += 1
            if not found == 2:
                atoms.remove(a)
                return atoms
    if DEBUG: print "Warning! Residue %s appears to be incomplete" % (atoms[0][17:20]+atoms[0][22:26]+atoms[0][21])
    return False
 

def findStacking(set1, set2 = None):
    """
    INPUT(set1, set2): scan the sets to find p- and t-stackings
    INPUT(set1): scan the set to find self-stackings (p-, t-)


    P-STACKING

        ---c---
           |
       A   V
       |
    ---c---       




    """
    DEBUG = 0

    MAXDIST_TSTACK = 5.0 # centroids distance (T-stacking)Angstroms 
    MAXDIST_PSTACK = 4.2 # centroids distance (P-stacking) Angstroms
    
    MAXDIST_PSTACK = MAXDIST_PSTACK**2
    MAXDIST_TSTACK = MAXDIST_TSTACK**2

    #MAXDIST = 5.0 # Angstroms
    #MAXDIST = MAXDIST**2

    PTOL = 29.9 # P-stacking plane angle tolerance (degr) TODO test values on a wide set!
    TTOL = 14.9 # T-stacking plane angle tolerance (degr) TODO test values on a wide set!
    PLANE_DIST_TSTACK = 2.5
    t_accepted = []
    p_accepted = []
    if not set2:
        set2 = set1
    for g1 in set1.keys():
        R1 = set1[g1]
        for g2 in set2.keys():
            if not g1 == g2: # this is for intramolecular stackings (set1 = set2)
                R2 = set2[g2]
                if not ([g1,g2] in p_accepted) and not ([g2,g1] in p_accepted):
                    if (not [g1,g2] in t_accepted) and not ([g2,g1] in t_accepted):
                        d = hf.quickdist(R1['centroid'], R2['centroid'])
                        if d <= MAXDIST_TSTACK:
                            #print "GOOD DIST: %2.3f" % sqrt(d),
                            pdist = abs(hf.dot( R1['normal'][0], (R1['centroid']-R2['centroid']) ))
                            pangle = abs(hf.vecAngle( R1['plane'], R2['plane']))
                            #print "DISTANCE: %2.2f <"% math.sqrt(d), math.sqrt(MAXDIST_TSTACK)
                            #print "PTOL", PTOL
                            #print "PDIST:", pdist 
                            #print "PANGLE:", pangle
                            #print "======"
                            #print "PANGLE-180", pangle-180
                            #print abs(pangle-180)<=PTOL or (pangle-PTOL)<=0
                            #print "PAANGLE-180 < PTOL", abs(pangle-180)<=PTOL
                            #print "PANGLE-PTOL", pangle-PTOL
                            #print "PANGLE-PTOL < 0", (pangle-PTOL)<=0
                            #print "\n\n"
                            if d <= MAXDIST_PSTACK and ((abs(pangle-180)<=PTOL) or ((pangle-PTOL)<=0)):
                                p_accepted.append([ g1, g2])
                                if DEBUG: 
                                    print " ==> P-stacking",
                                    print "%s--%s  plane angle: %2.1f | pdist: %2.2f\n\n" % (g1, g2, pangle, pdist), 
                            elif (( abs(pangle-90) <= TTOL) or ( abs(pangle-270)<=TTOL) ) and pdist < PLANE_DIST_TSTACK:
                                t_accepted.append([ g1, g2])
                                print "XXX"
                                if DEBUG:
                                    print "== > T-stacking",
                                    print "%s--%s  plane angle: %2.1f " % (g1, g2, pangle), 
                                    if ( abs(pangle-90) <= TTOL):
                                        print "ANGLE:",abs(pangle-90), "<", TTOL
                                    if ( abs(pangle-270)<=TTOL):
                                        print "ANGLE:", abs(pangle-270), "<", TTOL
                                    print "PLANE:",pdist, "<", PLANE_DIST_TSTACK
    return p_accepted, t_accepted 



def findRings(graph):
    """
    a very simple ring detection algorightm to identify 5, and 6 member aromatic rings

            A    <- head
           / \   
          B   C  <- tier 1
          |   |
          D   E  <- tier 2
           \ /
            F    <- tier 3, ring closure (6 member-ring)

    
            A    <- head 
           / \              
          B   C  <- tier 1
          |   |
          D---E  <- tier 2, ring closure (5-member ring)


            A   <- head 
            |             
            B   <- tier 1
           / \
          C---D <- tier 2  # SPURIOUS, RECOGNIZED BUT NOT COUNTED

              
    """
    # TODO add a planarity check?
    rings5 = []
    rings6 = []
    if DEBUG: print "- starting ring detection..."
    for head in graph.keys():
        tier1 = graph[head]
        tier2 = []
        tier3 = []
        # populate tier2 
        for node1 in tier1:
            for tmp in graph[node1]:
                if not tmp == head and not tmp in tier2 and (not tmp in tier1) :
                    tier2.append(tmp)
        # populate tier3
        for node2 in tier2:
            for tmp in graph[node2]:
                if (not tmp == head) and (not tmp in tier2) and (not tmp in tier1) and (not tmp in tier3):
                    tier3.append(tmp)
        # 6 member rings
        for x in tier3:
            candidate  = []
            for c in tier2:
                if x in graph[c]:
                    if not c in candidate:
                        candidate.append(c)
            if len(candidate) >1:
                r6 = [ head ] 
                r6.append(x)
                r6 += candidate
                for c in candidate:
                    r6 += hf.intersect( graph[head], graph[c])
                r6.sort()
                if not r6 in rings6:
                    rings6.append( r6 )
                    if DEBUG: print "    6member!", r6
                break
        # 5 member rings
        for c1 in tier2:
            for c2 in tier2:
                if not c1 == c2:
                    if (c2 in graph[c1]) and (c1 in graph[c2]):
                        is_3_ring = False
                        for k in graph[c1]:
                            if k in graph[c2]: 
                                is_3_ring =True
                                if DEBUG: print "       [ ...catched a cycle_3... ]"
                                break
                        if not is_3_ring :
                            r5 = [ head ] 
                            r5.append(c1)
                            r5.append(c2)
                            r5 += hf.intersect( graph[head], graph[c1])
                            r5 += hf.intersect( graph[head], graph[c2])
                            r5.sort()
                            if not r5 in rings5:
                                if DEBUG: print "    5member ring!",r5
                                rings5.append(r5)
                        break
    return rings5, rings6


def searchPiGroupsRec(rec):
    # input : rec atom lines (list)
    aromatic_residues, special = getAromaticRes(rec)
    arom_vectors = getResAromaticVectors(aromatic_residues)
    if special and DEBUG:
        print "INFO: found potential aromatic co-factors in the receptor [ %d ]" % len(special)
    return arom_vectors, special


def findLigandRings(atoms):
    matrix = hf.getDistMatrix(atoms)
    bdist = 2.0 # angstrom of bond dinstance
    graph = hf.makeGraph(nodes_list = range(len(matrix)), distance_matrix = matrix, cutoff = bdist**2)
    rings5,rings6 = findRings(graph)
    RING = rings5+rings6
    ligand_rings = {}
    for r in range(len(RING)):
        # res name first...
        
        # get the first atom PDB string in the ring
        atstring = atoms[RING[r][0]][2]
        ringname = hf.pmvAtomStrip(atstring) 
        ringname_short = ringname.rsplit(":",1)[0].strip()
        if ringname_short:
            c = 0
            while ringname_short+":"+str(c) in ligand_rings.keys():
                c+=1
                if c > 20:
                    ringname_short = None
                    break
        if ringname_short:
            lnam = ringname_short+":"+str(c) 
        else:
            lnam = "rng:"+str(r)

        ligand_rings[lnam] = []
        for a in RING[r]:
            ligand_rings[lnam].append(atoms[a][2])
    return ligand_rings

def searchPiGroupsLig(lig):
    # input : ligand atom lines (list)
    atoms = hf.getFlatAtoms(lig, flat_only = True)
    ligand_rings = findLigandRings(atoms)
    if ligand_rings:
        for r in ligand_rings.keys():
            if DEBUG: 
                print "+++"
                for a in ligand_rings[r]: print a[:-1]
                print "+++\n"
            ligand_rings[r] = atomsToVec(ligand_rings[r])
        return ligand_rings
    else:
        return False

def findLigRecPiStack(lig_atoms, rec_atoms = None, rec_vectors = None):
    # get the receptor aromatic vectors
    # if co-factors are present, process them with ligand tools
    """
    - REC: the function can be called with atoms or pre-calculated vectors
        if atoms:
            vectors will be calculated
        else:
            cached vectors will be used (special can be included too!)
    """
    if not rec_vectors:
        rec_vectors, special = searchPiGroupsRec(rec_atoms)
    if special:
        special = searchPiGroupsLig(special)
        if special:
            #rec_vectors += special
            rec_vectors.update(special)
    lig_vectors = searchPiGroupsLig(lig_atoms)
    pstack = []
    tstack = []
    if lig_vectors:
        lps, lts = findStacking(rec_vectors, lig_vectors)
        if DEBUG:
            if lps: print "Found P-stackings :", len(lps)
            if lts: print "Found T-stackings :", len(lts)
        if lps:
            for p in lps:
                res =  p[0]
                rec_centroid = rec_vectors[p[0]]['centroid']
                lig_centroid = lig_vectors[p[1]]['centroid'] 
                pstack.append([res, rec_centroid, lig_centroid]) 
        if lts:
            for p in lts:
                res =  p[0]
                rec_centroid = rec_vectors[p[0]]['centroid']
                lig_centroid = lig_vectors[p[1]]['centroid'] 
                tstack.append([res, rec_centroid, lig_centroid]) 
    return pstack, tstack

##################################################################
if __name__ == "__main__":
    from sys import argv
    import os
    
    # input must be PDBQT

    ligand = hf.getLines(argv[1])
    name = os.path.basename(argv[1])
    name = os.path.splitext(name)[0]

    try:
        if argv[2] =='-d':
            DEBUG=True
    except:
        pass

    lig_atoms = hf.getAtoms(ligand)
    ligand_rings = searchPiGroupsLig(lig_atoms)
    if not ligand_rings:
        print "No rings in the ligand"
        exit()
    else:
        outname = name+"_vector.pdb"
        print "Writing out centroid and normals [ %s ]" % outname

        out = open(outname, 'w')
        for i in ligand_rings:
            print "RING", i
            res = ligand_rings[i]
            for n in res['normal']:
                v = hf.vecSum( res['centroid'], n )
                out.write( hf.makePdb(coord=v)+'\n' )
            out.write( hf.makePdb(coord=res['centroid'])+'\n' )
        out.close()


