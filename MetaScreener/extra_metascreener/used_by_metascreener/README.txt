
  File name codification
==========================

Most of the files in this package are named following one of the next two
naming conventions:

1. {Simulation code}{Suffix}.{extension}

    * The 'simulation code' is a stochastic code to refer to this calculation.
    It is intended to be unique in our server in order to inequivocally point
    to this simulation.

    * The 'suffix' is a keyword indicative of the contents of the file. It is
    optional, and thus, not all files following this convention have a suffix.
    It usually starts with the '_' or the '-' characters, which are also used
    as word separators.

   * The 'extension' indicates which kind of content the file consists of.


2. {pose id}-BD-AD-receptor-ligand-{coordinates}{suffix}.{extension}

    Files following this convention are directly derived from docking experiments.

    * 'pose id' will be a number between 0 and the number of alpha carbons in
    the receptor. It indicates from which docking experiment the file is derived
    from.

    * The 'coordinates' represent the center of the grid box on which the docking
    was attempted. They are given in format {x}-{y}-{z}, using dashes as
    separators. Double dashes should be interpreted as a separator followed by
    a minus sign.

    * The 'suffixes' and the 'extensions' are used in the same way as in the
    first naming convention.



  Contents of the results package
====================================

{Simulation code}
|  >> Root directory in the results package.
|
├── README.txt
|     >> This file.
|
├── ligand.pdbqt
|     >> The original ligand, with which the docking experiments were performed,
|        in the '.pdbqt' format.
|
├── receptor.pdbqt
|     >> The original receptor, on which the docking experiments were performed,
|        in the '.pdbqt' format.
|
├── {Simulation code}.pse
|     >> A PyMOL session file, containing models for the recetor and every
|        clustered pose.
|
├── {Simulation code}.pml
|     >> A PyMOL script to reconstruct the {Simulation code}.pse session, in
|        case of trouble (ideally, you would never need it).
|        WARNING: this script should be use from a console terminal. Also,
|        since the script is heavily dependand on paths, 'receptor.pdbqt'
|        and the '.pdbqt' files for each clustered pose need to be in the
|        same directory as this script.
|
├── {Simulation code}_Clusters.txt
|     >> A text file detailing the bining energies and the number of docked poses
|        that overlapped on each cluster.
|
├── {Simulation code}_Clustered.png
|     >> A histogram of the binding affinities of the clustered poses (blue bars).
|        For the sake of comparison, the same histogram for raw poses is
|        superimposed in pink bars.
|
├── {Simulation code}_Unclustered.png
|     >> A histogram of the binding affinities of the raw, unclustered poses.
|        This is the same as the pink bars in the 'clustered' histogram.
|
├── {Simulation code}_Cluster_Affinity_Plot.png
|     >> A summary plot with the affinity breakdown for the best poses for each
|        detected cluster.
|
├── {Simulation code}_Cluster_Distances_Plot.png
|     >> A plot detailing the distances between the detected clusters.
|
├── raw_data/
|     >> These are the raw docking files before the clustering process.
|        For each pose, four files are given:
|            * a '.pdbqt' file, with the coordinates, partial charges and type
|            for each atom in the ligand after the docking calculation.
|            * a '.en' file, containing the energy details of the pose.
|            * two auxiliary '.txt' and '.ucm' files.
|
├── clustered_poses/
|     >> These are the raw docking files of the poses after the clustering step.
|        In this step, all spatially overlapping poses were clustered together,
|        and the pose with the best binding affinity was chosen as representative
|        for each cluster, and copied into this directory.
|        For each pose, several files are given (the number depends on if
|        flexibility for the receptor had been activated for the simulation):
|            * a '.pdbqt' file, with the coordinates, partial charges and type
|            for each atom in the ligand.
|            * a '.pdb' file, converted from each '.pdbqt' file.
|            * a '.en' file, containing the energy details of the pose.
|            * two auxiliary '.txt' and '.ucm' files.
|            * an optional '-flex.pdbqt' file, with the final data for the
|            residues that were considered as flexible. This file will only be
|            present if flexibility had
|            * two extra '.pdb' files: one containing the rigid part of the
|            receptor, and one containing the rigid receptor merged with the
|            final conformations of the flexible residues in the receptor. These
|            two files will only be present if flexibility for the receptor was
|            considered in the simulation.
|
├── clustered_affinities/
|     >> Plots showing binding energy breakdowns: one for the full ligand
|        ('-Global' suffix), and another one with a breakdown for each relevant
|        atom in the ligand ('-Atom' suffix). Also, a combined image of both
|        diagrams is supplied ('-Pack' suffix). One plot of every of these cases
|        is provided for each one of the clustered ligands.
|
├── clustered_interactions/
|     >> This directory contains the '_Complex.pdb' files used to detect the
|        interactions between the ligand and the surrounding residues for each
|        clustered pose.
|        For each clustered pose, a PyMOL session ('Interactions.txt.pse' file)
|        is provided, as well as a PyMOL script ('Interactions.txt.pml' file) to
|        reproduce it.
|        As the script in the root directory, these scripts are heavily path
|        dependant, and are meant to be run from a console terminal, but in this
|        case, to run a script, only the '_Complex.pdb' file corresponding to
|        same pose needs to be in the same directory as the script.
|        Also, a report on the interactions that have been found is provideded,
|        in the form of a plain text file ('_Interactions.txt' file).
|
└── (OPTIONAL) flexibility/
      >> This directory will only be present in simulations in which flexibility
         of the receptor had been activated. It contains multiple subfolders
         containing four files:
             * the receptor.pdbqt mentioned earlier.
             * receptor_rigid.pdbqt, the part of the receptor considered rigid.
             * receptor_flex.pdbqt, the residues of the receptor for which
             flexibility was considered in the simulation.
             * a '*-flex_str-*' file, with the specification of the residues
             that have been considered flexible.
