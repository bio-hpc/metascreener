# !/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

try:
    import pymol
except ImportError as e:
    print("ERROR: pymol not found")
    print(e)
    exit()


def prepare_complexes_pdb(prot_pdb, ligand_pdb, out_complex):
    """

    :param prot_pdb:
    :param ligand_pdb:
    :param out_complex:
    :Generate a pdb with the 2 structures joined
    """
    pymol.pymol_argv = ['pymol', '-c', '-q', '-k']
    pymol.finish_launching()

    pymol.cmd.reinitialize()
    pymol.cmd.set('max_threads', 1)

    pymol.cmd.load('{}'.format(ligand_pdb), object='lig')

    pymol.cmd.alter('all', 'resn="UNK"')

    pymol.cmd.load('{}'.format(prot_pdb), object='rec')

    if (len(pymol.cmd.get_chains('rec')) > 1):
        pymol.cmd.split_chains('rec')

        for x in pymol.cmd.get_names():
            if x == 'rec':
                for ch in pymol.cmd.get_chains(x):
                    if pymol.cmd.overlap('lig', 'rec_' + ch) == 0.0:
                        pymol.cmd.delete('rec_' + ch)
        pymol.cmd.delete('rec')

    pymol.cmd.save('{}'.format(out_complex))

    pymol.cmd.delete('all')


parser = argparse.ArgumentParser()
parser.add_argument('receptor_pdb', type=argparse.FileType('r'))
parser.add_argument('ligand_pdb', type=argparse.FileType('r'))
parser.add_argument('out_put_pdb', type=argparse.FileType('w'))
args = parser.parse_args()

prepare_complexes_pdb(args.receptor_pdb.name, args.ligand_pdb.name, args.out_put_pdb.name)
