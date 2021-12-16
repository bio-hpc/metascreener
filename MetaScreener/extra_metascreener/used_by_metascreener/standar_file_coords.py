#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# _______________________________________________________________________________________
#
#        Normalize pdbs, pdbqt and mol2 to format X:Y:Z:type:nAtom:Chain
#        example python standarFileCoords.py 3s5z.pdbqt
# ________________________________________________________________________________________-

import os
import sys

DELIMITER = ":"
OUTPUT_FMT = DELIMITER.join(('{0:.3f}', '{1:.3f}', '{2:.3f}', '{3}', '{4}', '{5}', '{6}', '{7}'))
BANNER = "##_____________________________________________\n" \
         "##\n" \
         "## X : Y : Z : type : nAtom : typeRes : NRes : Chain\n" \
         "##_____________________________________________\n" \

def f_mol2(funit):
    """
          1  O          1.6010   -0.2400    1.1620 O.2     1  LIG1       -0.2830
    """
    count = 0
    for line in funit:
        line = line.rstrip()
        if line.startswith("@<TRIPOS>BOND"):  
            count += 1
        if count == 1:
            if line !="":
                s = line.split()
                count_split = 0
                for i in s[7]:
                    count_split += 1
                    if i.isdigit():
                        break
                cadena = OUTPUT_FMT.format(
                    round(float(s[2]), 3),
                    round(float(s[3]), 3),
                    round(float(s[4]), 3),
                    s[1],
                    s[0],
                    s[7][:count_split - 1],
                    s[7][count_split - 1:],
		    ""
                )
                """
                cadena=\
                str(round(float(s[2]),3))+DELIMITER+\
                str(round(float(s[3]),3))+DELIMITER+\
                str(round(float(s[4]),3))+DELIMITER+\
                s[1]+DELIMITER+\
                s[0]+DELIMITER+\
                s[7][:count_split-1]+DELIMITER+\
                s[7][count_split-1:]
                """
                print(cadena)
        if line.startswith("@<TRIPOS>ATOM"):
            count += 1
    print(BANNER)


def f_pdb(funit):
    """
    Label ATOM
    COLUMNS        DATA TYPE       CONTENTS
    --------------------------------------------------------------------------------
     1 -  6        Record name     "ATOM  "
     7 - 11        Integer         Atom serial number.
    13 - 16        Atom            Atom name.
    17             Character       Alternate location indicator.
    18 - 20        Residue name    Residue name.
    22             Character       Chain identifier.
    23 - 26        Integer         Residue sequence number.
    27             AChar           Code for insertion of residues.
    31 - 38        Real(8.3)       Orthogonal coordinates for X in Angstroms.
    39 - 46        Real(8.3)       Orthogonal coordinates for Y in Angstroms.
    47 - 54        Real(8.3)       Orthogonal coordinates for Z in Angstroms.
    55 - 60        Real(6.2)       Occupancy.
    61 - 66        Real(6.2)       Temperature factor (Default = 0.0).
    73 - 76        LString(4)      Segment identifier, left-justified.
    77 - 78        LString(2)      Element symbol, right-justified.
    79 - 80        LString(2)      Charge on the atom.
    Example:
             1         2         3         4         5         6         7         8
    12345678901234567890123456789012345678901234567890123456789012345678901234567890

    ATOM    145  N   VAL A  25      32.433  16.336  57.540  1.00 11.92      A1   N
    """

    for line in funit:
        line = line.rstrip()
        if line.startswith("ATOM") or line.startswith("HETATM") and line != "":  # OJO los HETATM
            """
            cadena=line[0:6].strip()+DELIMITER+\
            line[6:11].strip ()+DELIMITER+\
            line[12:16].strip()+DELIMITER+\
            line[16:17].strip()+DELIMITER+\
            line[17:20].strip()+DELIMITER+\
            line[21:22].strip()+DELIMITER+\
            line[22:26].strip()+DELIMITER+\
            line[26:27].strip()+DELIMITER+\
            line[30:38].strip()+DELIMITER+\
            line[38:46].strip()+DELIMITER+\
            line[46:54].strip()+DELIMITER+\
            line[54:60].strip()+DELIMITER+\
            line[60:66].strip()+DELIMITER+\
            line[72:76].strip()+DELIMITER+\
            line[76:78].strip()+DELIMITER+\
            line[78:80].strip()
            """
            cadena = OUTPUT_FMT.format(
                round(float(line[30:38].strip()), 3),
                round(float(line[38:46].strip()), 3),
                round(float(line[46:54].strip()), 3),
                line[12:16].strip(),
                line[6:12].strip(),
                line[17:20].strip(),
                line[22:26].strip(),
                line[21:22].strip()
            )

            print(cadena)
        if line.startswith("CONECT"):
            break
    print(BANNER)


def f_pdbqt(funit):
    """
    pdbqt conversion

    1 - 6     Record name     "ATOM "
    7 - 11     Integer     serial     Atom serial number.
    13 - 16     Atom     name     Atom name.
    17     Character     altLoc     Alternate location indicator. IGNORED
    18 - 21     Residue name     resName     Residue name.
    22     Character     chainID     Chain identifier.
    23 - 26     Integer     resSeq     Residue sequence number.
    27     AChar     iCode     Code for insertion of residues. IGNORED
    31 - 38     Real(8.3)     x     Orthogonal coordinates for X in Angstroms.
    39 - 46     Real(8.3)     y     Orthogonal coordinates for Y in Angstroms.
    47 - 54     Real(8.3)     z     Orthogonal coordinates for Z in Angstroms.
    55 - 60     Real(6.2)     occupancy     Occupancy.
    61 - 66     Real(6.2)     tempFactor     Temperature factor.
    67 - 76     Real(10.4)     partialChrg     Gasteiger PEOE partial charge q.
    79 - 80     LString(2)     atomType     AutoDOCK atom type t. ##ESTE ESTA MAL es desde la 78
    ATOM     30  O   LIG    1       -5.496   1.759   0.000  0.00  0.00    -0.225 OA
    """
    # cad=[0,5,6,10,12,15,16,16,17,120]

    for line in funit:
        line = line.rstrip()
        if line.startswith("ATOM") or line.startswith("HETATM") and line != "":
            """
            cadena=line[0:6].strip()+DELIMITER+\
            line[6:11].strip ()+DELIMITER+\
            line[12:16].strip ()+DELIMITER+\
            line[16:17].strip ()+DELIMITER+\
            line[17:21].strip()+DELIMITER+\
            line[21:22].strip()+DELIMITER+\
            line[22:26].strip()+DELIMITER+\
            line[26:27].strip()+DELIMITER+\
            line[30:38].strip ()+DELIMITER+\
            line[38:46].strip()+DELIMITER+\
            line[46:54].strip()+DELIMITER+\
            line[54:60].strip()+DELIMITER+\
            line[60:66].strip()+DELIMITER+\
            line[66:76].strip()+DELIMITER+\
            line[76:77].strip()+DELIMITER+\
            line[77:80].strip()
            """
            cadena = OUTPUT_FMT.format(
                round(float(line[30:38].strip()), 3),
                round(float(line[38:46].strip()), 3),
                round(float(line[46:54].strip()), 3),
                line[12:16].strip(),
                line[6:11].strip(),
                line[17:21].strip(),
                line[22:26].strip(),
                line[21:22].strip()
            )

            print(cadena)
    print(BANNER)


def parse_file(fname):
    pybel.ob.obErrorLog.StopLogging()
    name, ext = os.path.splitext(fname)
    mol = pybel.readfile(ext.strip('.'), fname).next()

    for atm in mol.atoms:
        cadena = OUTPUT_FMT.format(
            atm.OBAtom.x(),
            atm.OBAtom.y(),
            atm.OBAtom.z(),
            atm.OBAtom.GetResidue().GetAtomID(atm.OBAtom).strip(),
            atm.OBAtom.GetIdx(),
            atm.OBAtom.GetResidue().GetName().strip(),
            atm.OBAtom.GetResidue().GetNum(),
            atm.OBAtom.GetResidue().GetChain().strip()
        )

        print(cadena)
    print(BANNER)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Enter target file")
        exit()

    fileEntrada = sys.argv[1]

    """parse_file(fileEntrada)"""

    filename, file_extension = os.path.splitext(sys.argv[1])

    f = open(fileEntrada)
    if file_extension == ".pdb":
        f_pdb(f)
    elif file_extension == ".mol2":
        f_mol2(f)
    elif file_extension == ".pdbqt":
        f_pdbqt(f)
    else:
        print("Error with target file")
    f.close()

