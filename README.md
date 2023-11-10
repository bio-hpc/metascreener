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

wget --no-check-certificate -r "https://drive.google.com/u/1/uc?export=download&confirm=TLUF&id=1L3HZ2l1XARqzEKaV14jToUtUOCmo4OjV" -O singularity/singularity.zip

unzip singularity/singularity.zip -d singularity/

rm singularity/singularity.zip

### Available Techniques
1. **Virtual Screening**
2. **Blind Docking**

### Available Software
1. **AD AutoDock Vina** 1.1.2 (May 11, 2011):
   Open source. https://github.com/ccsb-scripps/AutoDock-Vina.
2. **GN Gnina** v1.0.3 (Feb 11, 2023):  
   Open source. [https://github.com/ccsb-scripps/AutoDock-Vina](https://github.com/gnina/gnina).  
   Download the executable to metascreener/MetaScreener/external_sw/gnina/ and give execution permissions.                               
4. **LF Lead Finder** version 2104 build 1, 18 April 2021: 
   Commercial software. License and software required (copy to "metascreener/MetaScreener/external_sw/leadFinder/").
   You can get an Academic license at http://www.moltech.ru/leadfinder/versions.html.
5. **LS LigandScout** V4.4.7:
   Commercial software. License and software required (copy to "metascreener/MetaScreener/external_sw/ligandScout/").    
6. **DC Dragon** v.6.0.38:
   Commercial software. License and software required (copy to "metascreener//MetaScreener/external_sw/dragon/").
   
### Aditional Commercial software
1. **Poseview [Required ChemAxon]**:  generates publication-quality 2D structure-diagrams of protein-ligand complexes.
   Copy the software in "metascreener/MetaScreener/external_sw/poseview/" (Settings.pxx is provided).
   You can get an academic license at https://www.biosolveit.de/free-to-academics/.
2. **ChemAxon**: It is required in poseview for convert to mol2 format.
   Copy the software in "metascreener/MetaScreener/external_sw/"
   You can get an academic license at https://chemaxon.com/academic-license.
   
### extra_metascreener
It is a directory that contains multiple scripts used or related to metascreener. 

It is recommended to use these python scripts with the metascreener singularity image "metascreener/singularity/metascreener.simg". 
For instance:

singularity exec singularity/metasreener.simg python MetaScreener/extra_metascreener/convert/conv_to.py

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
