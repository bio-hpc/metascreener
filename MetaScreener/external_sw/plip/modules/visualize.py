"""
Protein-Ligand Interaction Profiler - Analyze and visualize protein-ligand interactions in PDB files.
visualize.py - Visualization of PLIP results using PyMOL.
Copyright 2014-2015 Sebastian Salentin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


# Own modules
from supplemental import initialize_pymol, start_pymol, write_message, colorlog, sysexit
import config
from pymolplip import PyMOLVisualizer
from plipremote import VisualizerData
from plip_logger import log

# Python Standard Library
import json
import sys

# Special imports
from pymol import cmd
import pymol


def select_by_ids(selname, idlist, selection_exists=False, chunksize=20, restrict=None):
    """Selection with a large number of ids concatenated into a selection
    list can cause buffer overflow in PyMOL. This function takes a selection
    name and and list of IDs (list of integers) as input and makes a careful
    step-by-step selection (packages of 20 by default)"""
    idlist = list(set(idlist))  # Remove duplicates
    if not selection_exists:
        cmd.select(selname, 'None')  # Empty selection first
        log("cmd.select('{}', 'None')  # Empty selection first\n".format(selname))
    idchunks = [idlist[i:i+chunksize] for i in xrange(0, len(idlist), chunksize)]
    for idchunk in idchunks:
        cmd.select(selname, '%s or (id %s)' % (selname, '+'.join(map(str, idchunk))))
        log("cmd.select('{0}', '{0} or (id {1})')\n".format(selname, '+'.join(map(str, idchunk))))
    if restrict is not None:
        cmd.select(selname, '%s and %s' % (selname, restrict))
        log("cmd.select('{0}', '{0} and {1}')\n".format(selname, restrict))


def visualize_in_pymol(plcomplex):
    """Visualizes the protein-ligand pliprofiler at one site in PyMOL."""

    vis = PyMOLVisualizer(plcomplex)



    #####################
    # Set everything up #
    #####################

    pdbid = plcomplex.pdbid
    lig_members = plcomplex.lig_members
    chain = plcomplex.chain
    if config.PEPTIDES != []:
        vis.ligname = 'PeptideChain%s' % plcomplex.chain

    ligname = vis.ligname
    hetid = plcomplex.hetid

    metal_ids = plcomplex.metal_ids
    metal_ids_str = '+'.join([str(i) for i in metal_ids])

    ########################
    # Basic visualizations #
    ########################

    start_pymol(run=True, options='-pcq', quiet=not config.DEBUG)
    vis.set_initial_representations()

    cmd.load(plcomplex.sourcefile)
    log("cmd.load('{}')\n".format(plcomplex.sourcefile.rsplit('/', 1)[-1]))
    current_name = cmd.get_object_list(selection='(all)')[0]
    write_message('Setting current_name to "%s" and pdbid to "%s\n"' % (current_name, pdbid), mtype='debug')
    cmd.set_name(current_name, pdbid)
    log("cmd.set_name('{}', '{}')\n".format(current_name, pdbid))
    cmd.hide('everything', 'all')
    log("cmd.hide('everything', 'all')\n")
    if config.PEPTIDES != []:
        cmd.select(ligname, 'chain %s and not resn HOH' % plcomplex.chain)
        log("cmd.select('{}', 'chain {} and not resn HOH')\n".format(ligname, plcomplex.chain))
    else:
        cmd.select(ligname, 'resn %s and chain %s and resi %s*' % (hetid, chain, plcomplex.position))
        log("cmd.select('{}', 'resn {} and chain {} and resi {}*')\n".format(ligname, hetid, chain, plcomplex.position))
    write_message("Selecting ligand for PDBID %s and ligand name %s with: " % (pdbid, ligname), mtype='debug')
    write_message('resn %s and chain %s and resi %s*' % (hetid, chain, plcomplex.position), mtype='debug')

    # Visualize and color metal ions if there are any
    if not len(metal_ids) == 0:
        vis.select_by_ids(ligname, metal_ids, selection_exists=True)
        cmd.show('spheres', 'id %s and %s' % (metal_ids_str, pdbid))
        log("cmd.show('spheres', 'id {} and {}')\n".format(metal_ids_str, pdbid))

    # Additionally, select all members of composite ligands
    if len(lig_members) > 1:
        for member in lig_members:
           resid, chain, resnr = member[0], member[1], str(member[2])
           cmd.select(ligname, '%s or (resn %s and chain %s and resi %s)' % (ligname, resid, chain, resnr))
           log("cmd.select({0}, '{0} or (resn {1} and chain {2} and resi {3})')\n".format(ligname, resid, chain, resnr))

    cmd.show('sticks', ligname)
    log("cmd.show('sticks', '{}')\n".format(ligname))
    cmd.color('myblue')
    log("cmd.color('myblue')\n")
    cmd.color('myorange', ligname)
    log("cmd.color('myorange', '{}')\n".format(ligname))
    cmd.util.cnc('all')
    log("cmd.util.cnc('all')\n")
    if not len(metal_ids) == 0:
        cmd.color('hotpink', 'id %s' % metal_ids_str)
        log("cmd.color('hotpink', 'id {}')\n".format(metal_ids_str))
        cmd.hide('sticks', 'id %s' % metal_ids_str)
        log("cmd.hide('sticks', 'id {}')\n".format(metal_ids_str))
        cmd.set('sphere_scale', 0.3, ligname)
        log("cmd.set('sphere_scale', 0.3, '{}')\n".format(ligname))
    cmd.deselect()
    log("cmd.deselect()\n")


    vis.make_initial_selections()

    vis.show_hydrophobic()  # Hydrophobic Contacts
    vis.show_hbonds()  # Hydrogen Bonds
    vis.show_halogen()  # Halogen Bonds
    vis.show_stacking()  # pi-Stacking Interactions
    vis.show_cationpi()  # pi-Cation Interactions
    vis.show_sbridges()  # Salt Bridges
    vis.show_wbridges()  # Water Bridges
    vis.show_metal()  # Metal Coordination

    vis.refinements()


    vis.zoom_to_ligand()

    vis.selections_cleanup()
    vis.selections_group()
    vis.additional_cleanup()
    if config.PEPTIDES == []:
        if config.PYMOL:
            vis.save_session(config.OUTPATH)
        if config.PICS:
            filename = '%s_%s' % (pdbid.upper(), "_".join([hetid, plcomplex.chain, plcomplex.position]))
            vis.save_picture(config.OUTPATH, filename)
    else:
        filename = "%s_PeptideChain%s" % (pdbid.upper(), plcomplex.chain)
        if config.PYMOL:
            vis.save_session(config.OUTPATH, override=filename)
        if config.PICS:
            vis.save_picture(config.OUTPATH, filename)
