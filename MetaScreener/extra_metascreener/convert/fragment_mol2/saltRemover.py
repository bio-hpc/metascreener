import argparse
from rdkit import Chem
from rdkit.Chem.SaltRemover import SaltRemover


parser = argparse.ArgumentParser(description='Remove fragments from mol2 file and prints smi without given elements')
optional = parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
required.add_argument('-f','--file', help='mol2 file', required=True)
required.add_argument('-d','--data', help='defnData for SaltRemover', required=True)
parser._action_groups.append(optional)
args = vars(parser.parse_args())

remover = SaltRemover(defnData=args['data'])
m = Chem.MolFromMol2File(args['file'])
res = remover.StripMol(m)

smi_in = Chem.MolToSmiles(m)
smi_out = Chem.MolToSmiles(res)

print smi_in
print smi_out
