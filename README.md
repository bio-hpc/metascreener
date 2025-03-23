## MetaScreener [(manual)](https://github.com/bio-hpc/metascreener/wiki)
MetaScreener is a collection of scripts developed in different languages (Shell script, Python, Java and C) that integrates, among others, docking, similarity and molecular modeling programs, through which jobs are sent to slurm on supercomputers and the data is processed automatically by sorting it into tables and graphs. It has been developed by the Structural Bioinformatics and High Performance Computing (BIO-HPC, https://bio-hpc.eu) at UCAM Universidad Católica de Murcia.

### Installation (choose one)
1. git clone https://github.com/bio-hpc/metascreener.git
2. git clone git@github.com:bio-hpc/metascreener.git
3. gh repo clone bio-hpc/metascreener
4. Download the .zip and unzip it in the supercomputing centers you are going to use 

### Download singularity image 
Needed to secure compatibility with the HPC cluster.

cd metascreener/

wget --no-check-certificate -r "https://drive.usercontent.google.com/download?id=1L3HZ2l1XARqzEKaV14jToUtUOCmo4OjV&export=download&authuser=1&confirm=t&uuid=0c83343d-17fe-4282-bf07-9a2321537a9a&at=APZUnTW_78yhd6klINcZBOjxIU6g:1706872870521" -O singularity/singularity.zip

unzip singularity/singularity.zip -d singularity/

rm singularity/singularity.zip

### Available Techniques
1. **Virtual Screening**
2. **Blind Docking**

### Available Software
1. **AD AutoDock Vina** 1.1.2 (May 11, 2011):
   Open source. https://github.com/ccsb-scripps/AutoDock-Vina.
2. **GN Gnina** v1.3 (Oct 4, 2024):  
   Open source. https://github.com/gnina/gnina.  
   Download the [executable](https://github.com/gnina/gnina/releases/tag/v1.3) to metascreener/MetaScreener/external_sw/gnina/ and give execution permissions.                               
4. **LF Lead Finder** version 2104 build 1, 18 April 2021: 
   Commercial software. License and software required (copy to "metascreener/MetaScreener/external_sw/leadFinder/").
   You can get an Academic license at http://www.moltech.ru/leadfinder/versions.html.
5. **LS LigandScout** V4.4.7:
   Commercial software. License and software required (copy to "metascreener/MetaScreener/external_sw/ligandScout/").    
6. **DC Dragon** v.6.0.38:
   Commercial software. License and software required (copy to "metascreener/MetaScreener/external_sw/dragon/").
7. **EO EON** v2.4.2.3:
   Commercial software. License and software required (copy to "metascreener/MetaScreener/external_sw/openeye/eon/").
8. **RC ROCS** v3.6.1.3:
   Commercial software. License and software required (copy to "metascreener/MetaScreener/external_sw/openeye/rocs/").
   
### Aditional Commercial software
1. **Poseview [Required ChemAxon]**:  generates publication-quality 2D structure-diagrams of protein-ligand complexes.
   Copy the software in "metascreener/MetaScreener/external_sw/poseview/" (Settings.pxx is provided).
   You can get an academic license at https://www.biosolveit.de/free-to-academics/.
2. **ChemAxon**: It is required in poseview for convert to mol2 format.
   Copy the software in "metascreener/MetaScreener/external_sw/"
   You can get an academic license at https://chemaxon.com/academic-license.
### ESSENCE-Dock
ESSENCE-Dock can take in docking runs from different algorithms, and uses all of the information to rescore the compounds using a consensus-based approach.
For more information about ESSENCE-Dock, you check out the manuscript [here](https://pubs.acs.org/doi/10.1021/acs.jcim.3c01982).
To use ESSENCE-Dock, you need to make sure the individual docking calculations used `metascreener`, finished correctly and contain a `Results_scoring.csv`. If this is not present, or if you moved the directory you can regenerate the file using:  
 ```
python MetaScreener/extra_metascreener/used_by_metascreener/get_csv.py <docking directory>
 ```
After that, you can use ESSENCE-Dock:
 ```
./MetaScreener/extra_metascreener/results/ESSENCE-Dock.sh -f <docking_dir1> <docking_dir2> ... -p <proteinFile> -out <output_dir>
 ```
There are many more options (like running using slurm, configuring the amount of cores to run on, ...). For more information you can also always use the help command (`./MetaScreener/extra_metascreener/results/ESSENCE-Dock.sh`) or feel free to open a GitHub issue.   
### extra_metascreener
It is a directory that contains multiple scripts used or related to metascreener. 

It is recommended to use these python scripts with the metascreener singularity image "metascreener/singularity/metascreener.simg". 
For instance:

singularity exec singularity/metascreener.simg python MetaScreener/extra_metascreener/convert/conv_to.py

#### convert
- **conv_to.py***: Convert molecule folders between sdf, pdb, pdbqt and mol2 formats. *Requires ChemAxom for mol2 conversions 
- **saltRemover.py [Required ChemAxon]**: Remove fragments from mol2 file and prints smi without given elements.
- **frament_mol2.sh**: Use **saltRemover.py** with the indicated salt remover by adding molecules to Cl,Br.
#### launchers
- **launcher_bd.sh**: Launch Blind Dockings with AutoDock Vina or Lead Finder from a protein directory and a ligand directory. 
- **launcher_ls.sh**: Launch virtual screening with LigandScout for 0 to a given number of omitted features (default 0 to 5).
#### results
- **analyse_residues_plip.py**: Script to analyze a set of Blind Docking results by residues.
- **cross_list_bd.py**: Cluster binding of Blind Docking with different ligands or the same.
- **cross_list_vs.py**: Cross virtual screening lists with different docking programs.
- **join_cl_json_bd_session.py**: It makes a PyMol session with the results obtained by cross_list_bd.py.
- **join_cl_json_vs_session.py**:It makes a PyMol session with the results obtained by cross_list_vs.py
- **join_ls_sessions.py**: It joins experiments carried out with LigandScout in MetaScreener into a single file to view it in LigandScout and excel.
 Excel files are generated in .csv and .xlsx.
#### used_by_metascreener
Scripts used internally by metascreener to process the results. 
#### utils
- **distance_ligand_point-py**: Calculate the distance between a ligand and a point.
