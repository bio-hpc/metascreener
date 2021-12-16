#!/bin/bash

defnData="[Cl,Br]"

helpFunction()
{
   echo ""
   echo "Usage: $0 -d path"
   echo -e "\t-d Path with mol2 files"
   echo -e  "\t-m Define salt remover by adding molecules to Cl,Br. Enter separated by commas and without white spaces. Default [Cl,Br]."
   exit 1 # Exit script after printing help
}

while getopts "d:m:h" opt
do
   case "$opt" in
      d ) path="$OPTARG" ;;
      m ) molec="$OPTARG" ;;
      h ) helpFunction ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$path" ]
then
   echo "You must indicate a directory";
   helpFunction
fi

if [ -n "$molec" ]
then
  defnData="[Cl,Br,$molec]"
fi

echo "Using SaltRemove with $defnData"

files=`find $path -type f -name "*.mol2" -exec grep -l "fragment" {} \;`

for file in $files
do
  smi=($(python MetaScreener/extra_metascreener/convert/fragment_mol2/saltRemover.py -f $file -d $defnData))
  smi_in=${smi[0]}
  smi_out=${smi[1]}

  if [ $smi_in == $smi_out ]; then
    echo "SaltRemove has not produced any changes to the compound. We select the longest fragment"
    smi_out=""
    len_out=0
    for s in $(echo $smi_in | tr "." "\n" )
    do
      len=$(echo -n $s | wc -m)
      if [ $len -gt $len_out ]; then
        smi_out=$s
        len_out=$len
      fi
    done
  fi

  echo "Input smiles: $smi_in"
  echo "Output smiles: $smi_out"
  file_out=$(basename $file)"_mod.mol2"
  mv $file $file.bk
  ./MetaScreener/external_sw/ChemAxon/JChem/bin/molconvert -3:e mol2 $smi_out -o $file
  
done
