import pdb
from FlexTree.FTRotamers import  FTRotamer, RotamerLib
libFile='FlexTree/bbind02.May.lib'
defFile='FlexTree/rotamer.def'
preloadedLib = RotamerLib(libFile,defFile )
lib=preloadedLib
confFile='FlexTree/AminoAcids.pdb'

from MolKit import Read
m = Read(confFile)[0]
m.buildBondsByDistance()
residues = m.chains[0].residues

datafile=open('RotLib1.py','w')
datafile.write("### rotamer library . Yong Zhao, TSRI, 2005 \n")
rotamerLib={}
names=residues.name

# no rotamer for GLY and ALA
del names[names.index('GLY42')]
del names[names.index('ALA45')]

for resName in names:
    fragment = residues.get(resName)[0]
    name = resName[:3]  # ARG17 -> ARG
    angDef, angList = lib.get(name)
    rotamer = FTRotamer(residue=fragment, angleDef=angDef,
                        angleList=angList , name=name+"_Rotamer")
    confs=[]
    for i in range(rotamer.num_conformation):
        conf = rotamer.getConf(i)
        confs.append(conf)
    rotamerLib[name]  = confs

datafile.write('RotLib=')
data=str(rotamerLib)
datafile.write(data)
datafile.write('\n')

datafile.close()
