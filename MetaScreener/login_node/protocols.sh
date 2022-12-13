#!/bin/bash
printTitle()
{
  if [ "$option" != "PROTOCOLS" ];then
    echo ""
  fi
  printf "${GREEN} %-20s ${YELLOW}%-30s${NONE} \n" "$1" "$2" 

} 
printTitle1()
{
  if [ "$option" != "PROTOCOLS" ];then
   # a=`echo $1 | sed 's/\\\t/\ /g'`
    printf "${PURPLE} %8s ${CYAN}%-30s${NONE}  \n" "${1}º" "$2" 
  fi
} 
printTitle2()
{
 if [ "$option" != "PROTOCOLS" ];then
    #a=`echo $1 | sed 's/\\\t/\ /g'`
    printf "${DARKGRAY} %10s ${CYAN}%-50s${NONE}  \n" "$1" "$2" 
  fi
} 
printTitle3()
{
 if [ "$option" != "PROTOCOLS" ];then
    #a=`echo $1 | sed 's/\\\t/\ /g'`
    printf "${DARKGRAY} %13s ${CYAN}%-20s${NONE}  \n" "$1" "$2" 
  fi
} 

echo ""
printTitle "PDBQT_ADT_PROT" "ADT Receptor"
printTitle1 "1" "We cut into monomers or as appropriate, looking at the info of the PDB using pymol "
printTitle1 "2" "We open the resulting pdb in ADT"
printTitle2 "2.a" "Edit -> Delete water "
printTitle2 "2.b" "Edit -> Hydrogens -> ADD"
printTitle2 "2.c" "Edit -> Atoms -> AssignAd4Type"
printTitle2 "2.d" "Edit -> Charges -> compute Gasteiger"
printTitle1 "3" "File -> save -> Write pdbqt"

printTitle "PDBQT_ADT_LIG" "ADT Ligand"
printTitle1 "1" "Ligand -> Input -> Open -> pdb"
printTitle1 "2" "Edit -> Charges -> Compute Gasteiger"
printTitle1 "3" "File -> save -> Write pdbqt"

printTitle "PDBQT_MGTOOLS_PROT" "MGTOOLS Receptor"
printTitle1 "1" "We cut into monomers or as appropriate, looking at the info of the PDB using pymol "
printTitle1 "2" "We use script prepare_receptor: "
printTitle2 "2.a" "pythonsh prepare_receptor4.py -r receptor.pdbqt -o outReceptor.pdbqt"" -A checkhydrogens"
      

printTitle "PDBQT_MGTOOLS_LIG" "MGTOOLS Receptor"
printTitle1 "1" "We use script prepare_ligand4"
printTitle2 "1.a" "pythonsh prepare_ligand4.py -l query.pdbqt -o outLigand.pdbqt -A 'hydrogens' -U \'\'"

printTitle "MOL2_MOE_PROT" "Moe Receptor"
printTitle1 "1" "We cut into monomers or as appropriate, looking at the info of the PDB using pymol "
printTitle1 "2" "Open Moe"
printTitle2 "2.a" "File-> Open->protein.pdb"
printTitle3 "2.a.a" "Check Ignore Water"
printTitle2 "2.b" "Edit -> hydrogens -> Add Polars Hydrogens"
printTitle2 "2.c" "Compute -> Partial Carges"
printTitle3 "2.c.a" "Method -> Amber 99"
printTitle3 "2.c.b" "Options \"check\" Adjust hidrogens and Lone Pairs"
printTitle2 "2.d" "Compute->Energy Minimize -> ok"
printTitle2 "2.e" "File -> save"

printTitle "MOL2_MOE_LIG" "Moe Ligand"
printTitle1 "1" "Open Moe"
printTitle2 "1.a" "New -> Database"
printTitle2 "1.b" "File-> import->ligand_library.sdf"
printTitle2 "1.c" "Wash -> click neutralize acid and base, rest default (remove salts)"
printTitle2 "1.d" "Compute Molecule Name-> field -> ID or name.. (this sets name of molecule)"
printTitle2 "1.e" "Compute -> Partial Carges"
printTitle3 "1.e.a" "Method -> Gasteiger"
printTitle3 "1.e.b" "Options \"check\" Adjust hidrogens and Lone Pairs ... (dont check if dont want to change hydrogens)"
printTitle2 "1.f" "Compute->Energy Minimize -> ok"
printTitle2 "1.g" "File -> export"
printTitle3 "1.g.a" "Chose format (default mdb)"
printTitle2 "1.h" "File -> save"

printTitle "CONF_OMEGA" "OMEEGA CONFOMATION"
printTitle1 "1" "Take library previously prepared by MOE as in Ligand preparation for Docking"

printTitle "AD_RECEPTOR_NM" "MGTools Receptor without modifications"
printTitle1 "1" "pythonsh prepare_receptor4.py -r receptor.pdbqt -o outReceptor.pdbqt"

printTitle "AD_LIGAND_NM" "MGTools Ligando without modifications"
printTitle1 "1" "pythonsh prepare_ligand4.py -l query.pdbqt -o outLigand.pdbqt"

printTitle "LF_RECEPTOR_NM" "MOE Receptor  without modifications"
printTitle1 "1" "Open Moe"
printTitle2 "1.a" "File-> Open->protein.pdb"
printTitle2 "1.b" "File -> save mol2"

printTitle "LF_LIGAND_NM" "MOE Ligand without modifications"
printTitle1 "1" "Open Moe"
printTitle2 "1.a" "File-> Open->protein.pdb"
printTitle2 "1.b" "File -> save mol2"

echo ""
echo ""
