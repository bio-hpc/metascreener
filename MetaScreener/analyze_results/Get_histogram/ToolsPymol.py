#!/usr/bin/env python
# -*- coding: utf-8 -*-
CORES = 1

try:
    import pymol
except ImportError as e:
    print("ERROR: pymol")
    print(e)
    exit()


def prepare_complexes_pdb( prot_pdb, ligand_pdb, out_complex):
    """

    :param prot_pdb:
    :param ligand_pdb:
    :param out_complex:
    :Generates a pdb with 2 structures attached
    """
    pymol.pymol_argv = ['pymol', '-c', '-q', '-k']
    pymol.finish_launching()
    pymol.cmd.reinitialize()
    pymol.cmd.set('max_threads', CORES)
    pymol.cmd.load('{}'.format(ligand_pdb), object='lig')
    pymol.cmd.alter('lig', "resn='LIG'")
    pymol.cmd.alter('lig', "resi='0'")
    pymol.cmd.load('{}'.format(prot_pdb), object='rec')
    pymol.cmd.select( 'com', '*')
    pymol.cmd.save('{}'.format(out_complex))
    pymol.cmd.delete('all')


def get_select_around_x_to_res(complex, out_put_complex, residue, distance):

    pymol.pymol_argv = ['pymol', '-c', '-q', '-k']
    pymol.finish_launching()
    pymol.cmd.reinitialize()
    pymol.cmd.set('max_threads', CORES)
    pymol.cmd.load('{}'.format(complex), object='residue')

    pymol.cmd.select('pocket', 'resname {} resname {} around {}'.format(residue, residue, distance))
    pymol.stored.list = []
    pymol.cmd.iterate("pocket", "stored.list.append(resi)")
    pymol.cmd.save(out_put_complex, 'pocket')

