"""
Protein-Ligand Interaction Profiler - Analyze and visualize protein-ligand interactions in PDB files.
pymolplip.py - Visualization class for PyMOL.
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
from pymol import cmd #, get_version_message
from time import sleep
import sys
import os
import subprocess

from plip_logger import init_logging, log, write_log

class PyMOLVisualizer:

    def __init__(self, plcomplex):
        if not plcomplex is None:
            self.plcomplex = plcomplex
            self.protname = plcomplex.pdbid  # Name of protein with binding site
            self.hetid = plcomplex.hetid
            self.ligname = "Ligand_" + self.hetid  # Name of ligand
            self.metal_ids = plcomplex.metal_ids
            init_logging()

    def set_initial_representations(self):
        """General settings for PyMOL"""
        self.standard_settings()
        cmd.set('dash_gap', 0)  # Show not dashes, but lines for the pliprofiler
        log("cmd.set('dash_gap', 0)  # Show not dashes, but lines for the pliprofiler\n")
        cmd.set('ray_shadow', 1)  # Turn on ray shadows for clearer ray-traced images
        log("cmd.set('ray_shadow', 1)  # Turn on ray shadows for clearer ray-traced images\n")
        # cmd.set('cartoon_color', 'mylightblue')
        # log("cmd.set('cartoon_color', 'mylightblue')\n")

        # Set clipping planes for full view
        cmd.clip('far', -1000)
        log("cmd.clip('far', -1000)\n")
        cmd.clip('near', 1000)
        log("cmd.clip('near', 1000)\n")

    def make_initial_selections(self):
        """Make empty selections for structures and interactions"""
        for group in ['Hydrophobic-P', 'Hydrophobic-L', 'HBondDonor-P',
        'HBondDonor-L', 'HBondAccept-P', 'HBondAccept-L',
        'HalogenAccept', 'HalogenDonor', 'Water', 'MetalIons', 'StackRings-P',
        'PosCharge-P', 'PosCharge-L', 'NegCharge-P', 'NegCharge-L',
        'PiCatRing-P', 'StackRings-L', 'PiCatRing-L', 'Metal-M', 'Metal-P',
        'Metal-W', 'Metal-L', 'Unpaired-HBA', 'Unpaired-HBD', 'Unpaired-HAL',
        'Unpaired-RINGS']:
            cmd.select(group, 'None')
            log("cmd.select('{}', 'None')\n".format(group))

    def standard_settings(self):
        """Sets up standard settings for a nice visualization."""
        # cmd.set('bg_rgb', [1.0, 1.0, 1.0])  # White background
        # log("cmd.set('bg_rgb', [1.0, 1.0, 1.0])  # White background\n")
        cmd.set('depth_cue', 0)  # Turn off depth cueing (no fog)
        log("cmd.set('depth_cue', 0)  # Turn off depth cueing (no fog)\n")
        cmd.set('cartoon_side_chain_helper', 1)  # Improve combined visualization of sticks and cartoon
        log("cmd.set('cartoon_side_chain_helper', 1)  # Improve combined visualization of sticks and cartoon\n")
        cmd.set('cartoon_fancy_helices', 1)  # Nicer visualization of helices (using tapered ends)
        log("cmd.set('cartoon_fancy_helices', 1)  # Nicer visualization of helices (using tapered ends)\n")
        cmd.set('transparency_mode', 1)  # Turn on multilayer transparency
        log("cmd.set('transparency_mode', 1)  # Turn on multilayer transparency\n")
        cmd.set('dash_radius', 0.05)
        log("cmd.set('dash_radius', 0.05)\n")
        self.set_custom_colorset()

    def set_custom_colorset(self):
        """Defines a colorset with matching colors. Provided by Joachim."""
        cmd.set_color('myorange', '[253, 174, 97]')
        log("cmd.set_color('myorange', '[253, 174, 97]')\n")
        cmd.set_color('mygreen', '[171, 221, 164]')
        log("cmd.set_color('mygreen', '[171, 221, 164]')\n")
        cmd.set_color('myred', '[215, 25, 28]')
        log("cmd.set_color('myred', '[215, 25, 28]')\n")
        cmd.set_color('myblue', '[43, 131, 186]')
        log("cmd.set_color('myblue', '[43, 131, 186]')\n")
        cmd.set_color('mylightblue', '[158, 202, 225]')
        log("cmd.set_color('mylightblue', '[158, 202, 225]')\n")
        cmd.set_color('mylightgreen', '[229, 245, 224]')
        log("cmd.set_color('mylightgreen', '[229, 245, 224]')\n")

    def select_by_ids(self, selname, idlist, selection_exists=False, chunksize=20, restrict=None):
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


    def object_exists(self, object_name):
        """Checks if an object exists in the open PyMOL session."""
        return object_name in cmd.get_names("objects")

    def show_hydrophobic(self):
        """Visualizes hydrophobic contacts."""
        hydroph = self.plcomplex.hydrophobic_contacts
        if not len(hydroph.bs_ids) == 0:
            self.select_by_ids('Hydrophobic-P', hydroph.bs_ids, restrict=self.protname)
            self.select_by_ids('Hydrophobic-L', hydroph.lig_ids, restrict=self.ligname)
            for i in hydroph.pairs_ids:
                cmd.select('tmp_bs', 'id %i & %s' % (i[0], self.protname))
                log("cmd.select('tmp_bs', 'id {} & {}')\n".format(i[0], self.protname))
                cmd.select('tmp_lig', 'id %i & %s' % (i[1], self.ligname))
                log("cmd.select('tmp_lig', 'id {} & {}')\n".format(i[1], self.ligname))
                cmd.distance('Hydrophobic', 'tmp_bs', 'tmp_lig')
                log("cmd.distance('Hydrophobic', 'tmp_bs', 'tmp_lig')\n")
            if self.object_exists('Hydrophobic'):
                cmd.set('dash_gap', 0.5, 'Hydrophobic')
                log("cmd.set('dash_gap', 0.5, 'Hydrophobic')\n")
                cmd.set('dash_color', 'grey50', 'Hydrophobic')
                log("cmd.set('dash_color', 'grey50', 'Hydrophobic')\n")
        else:
            cmd.select('Hydrophobic-P', 'None')
            log("cmd.select('Hydrophobic-P', 'None')\n")

    def show_hbonds(self):
        """Visualizes hydrogen bonds."""
        hbonds = self.plcomplex.hbonds
        for group in [['HBondDonor-P', hbonds.prot_don_id],
        ['HBondAccept-P', hbonds.prot_acc_id]]:
            if not len(group[1]) == 0:
                self.select_by_ids(group[0], group[1], restrict=self.protname)
        for group in [['HBondDonor-L', hbonds.lig_don_id],
        ['HBondAccept-L', hbonds.lig_acc_id]]:
            if not len(group[1]) == 0:
                self.select_by_ids(group[0], group[1], restrict=self.ligname)
        for i in hbonds.ldon_id:
            cmd.select('tmp_bs', 'id %i & %s' % (i[0], self.protname))
            log("cmd.select('tmp_bs', 'id {} & {}')\n".format(i[0], self.protname))
            cmd.select('tmp_lig', 'id %i & %s' % (i[1], self.ligname))
            log("cmd.select('tmp_lig', 'id {} & {}')\n".format(i[1], self.ligname))
            cmd.distance('HBonds', 'tmp_bs', 'tmp_lig')
            log("cmd.distance('HBonds', 'tmp_bs', 'tmp_lig')\n")
        for i in hbonds.pdon_id:
            cmd.select('tmp_bs', 'id %i & %s' % (i[1], self.protname))
            log("cmd.select('tmp_bs', 'id {} & {}')\n".format(i[1], self.protname))
            cmd.select('tmp_lig', 'id %i & %s' % (i[0], self.ligname))
            log("cmd.select('tmp_lig', 'id {} & {}')\n".format(i[0], self.ligname))
            cmd.distance('HBonds', 'tmp_bs', 'tmp_lig')
            log("cmd.distance('HBonds', 'tmp_bs', 'tmp_lig')\n")
        if self.object_exists('HBonds'):
            cmd.set('dash_color', 'blue', 'HBonds')
            log("cmd.set('dash_color', 'blue', 'HBonds')\n")

    def show_halogen(self):
        """Visualize halogen bonds."""
        halogen = self.plcomplex.halogen_bonds
        all_don_x, all_acc_o = [], []
        for h in halogen:
            all_don_x.append(h.don_id)
            all_acc_o.append(h.acc_id)
            cmd.select('tmp_bs', 'id %i & %s' % (h.acc_id, self.protname))
            log("cmd.select('tmp_bs', 'id {} & {}')\n".format(h.acc_id, self.protname))
            cmd.select('tmp_lig', 'id %i & %s' % (h.don_id, self.ligname))
            log("cmd.select('tmp_lig', 'id {} & {}')\n".format(h.don_id, self.ligname))

            cmd.distance('HalogenBonds', 'tmp_bs', 'tmp_lig')
            log("cmd.distance('HalogenBonds', 'tmp_bs', 'tmp_lig')\n")
        if not len(all_acc_o) == 0:
            self.select_by_ids('HalogenAccept', all_acc_o, restrict=self.protname)
            self.select_by_ids('HalogenDonor', all_don_x, restrict=self.ligname)
        if self.object_exists('HalogenBonds'):
            cmd.set('dash_color', 'greencyan', 'HalogenBonds')
            log("cmd.set('dash_color', 'greencyan', 'HalogenBonds')\n")

    def show_stacking(self):
        """Visualize pi-stacking interactions."""
        stacks = self.plcomplex.pistacking
        for i, stack in enumerate(stacks):
            pires_ids = '+'.join(map(str, stack.proteinring_atoms))
            pilig_ids = '+'.join(map(str, stack.ligandring_atoms))
            cmd.select('StackRings-P', 'StackRings-P or (id %s & %s)' % (pires_ids, self.protname))
            log("cmd.select('StackRings-P', 'StackRings-P or (id {} & {})')\n".format(pires_ids, self.protname))
            cmd.select('StackRings-L', 'StackRings-L or (id %s & %s)' % (pilig_ids, self.ligname))
            log("cmd.select('StackRings-L', 'StackRings-L or (id %s & %s)')\n".format(pilig_ids, self.ligname))
            cmd.select('StackRings-P', 'byres StackRings-P')
            log("cmd.select('StackRings-P', 'byres StackRings-P')\n")
            cmd.show('sticks', 'StackRings-P')
            log("cmd.show('sticks', 'StackRings-P')\n")

            cmd.pseudoatom('ps-pistack-1-%i' % i, pos=stack.proteinring_center)
            log("cmd.pseudoatom('ps-pistack-1-{}', pos={})\n".format(i, stack.proteinring_center))
            cmd.pseudoatom('ps-pistack-2-%i' % i, pos=stack.ligandring_center)
            log("cmd.pseudoatom('ps-pistack-2-{}', pos={})\n".format(i, stack.ligandring_center))
            cmd.pseudoatom('Centroids-P', pos=stack.proteinring_center)
            log("cmd.pseudoatom('Centroids-P', pos={})\n".format(stack.proteinring_center))
            cmd.pseudoatom('Centroids-L', pos=stack.ligandring_center)
            log("cmd.pseudoatom('Centroids-L', pos={})\n".format(stack.ligandring_center))

            if stack.type == 'P':
                cmd.distance('PiStackingP', 'ps-pistack-1-%i' % i, 'ps-pistack-2-%i' % i)
                log("cmd.distance('PiStackingP', 'ps-pistack-1-{0}', 'ps-pistack-2-{0}')\n".format(i))
            if stack.type == 'T':
                cmd.distance('PiStackingT', 'ps-pistack-1-%i' % i, 'ps-pistack-2-%i' % i)
                log("cmd.distance('PiStackingT', 'ps-pistack-1-{0}', 'ps-pistack-2-{0}')\n".format(i))
        if self.object_exists('PiStackingP'):
            cmd.set('dash_color', 'green', 'PiStackingP')
            log("cmd.set('dash_color', 'green', 'PiStackingP')\n")
            cmd.set('dash_gap', 0.3, 'PiStackingP')
            log("cmd.set('dash_gap', 0.3, 'PiStackingP')\n")
            cmd.set('dash_length', 0.6, 'PiStackingP')
            log("cmd.set('dash_length', 0.6, 'PiStackingP')\n")
        if self.object_exists('PiStackingT'):
            cmd.set('dash_color', 'smudge', 'PiStackingT')
            log("cmd.set('dash_color', 'smudge', 'PiStackingT')\n")
            cmd.set('dash_gap', 0.3, 'PiStackingT')
            log("cmd.set('dash_gap', 0.3, 'PiStackingT')\n")
            cmd.set('dash_length', 0.6, 'PiStackingT')
            log("cmd.set('dash_length', 0.6, 'PiStackingT')\n")

    def show_cationpi(self):
        """Visualize cation-pi interactions."""
        for i, p in enumerate(self.plcomplex.pication):
            cmd.pseudoatom('ps-picat-1-%i' % i, pos=p.ring_center)
            log("cmd.pseudoatom('ps-picat-1-{}', pos={})\n".format(i, p.ring_center))
            cmd.pseudoatom('ps-picat-2-%i' % i, pos=p.charge_center)
            log("cmd.pseudoatom('ps-picat-2-{}', pos={})\n".format(i, p.charge_center))
            if p.protcharged:
                cmd.pseudoatom('Chargecenter-P', pos=p.charge_center)
                log("cmd.pseudoatom('Chargecenter-P', pos={})\n".format(p.charge_center))
                cmd.pseudoatom('Centroids-L', pos=p.ring_center)
                log("cmd.pseudoatom('Centroids-L', pos={})\n".format(p.ring_center))
                pilig_ids = '+'.join(map(str, p.ring_atoms))
                cmd.select('PiCatRing-L', 'PiCatRing-L or (id %s & %s)' % (pilig_ids, self.ligname))
                log("cmd.select('PiCatRing-L', 'PiCatRing-L or (id {} & {})')\n".format(pilig_ids, self.ligname))
                for a in p.charge_atoms:
                    cmd.select('PosCharge-P', 'PosCharge-P or (id %i & %s)' % (a, self.protname))
                    log("cmd.select('PosCharge-P', 'PosCharge-P or (id {} & {})')\n".format(a, self.protname))
            else:
                cmd.pseudoatom('Chargecenter-L', pos=p.charge_center)
                log("cmd.pseudoatom('Chargecenter-L', pos={})\n".format(p.charge_center))
                cmd.pseudoatom('Centroids-P', pos=p.ring_center)
                log("cmd.pseudoatom('Centroids-P', pos={})\n".format(p.ring_center))
                pires_ids = '+'.join(map(str, p.ring_atoms))
                cmd.select('PiCatRing-P', 'PiCatRing-P or (id %s & %s)' % (pires_ids, self.protname))
                log("cmd.select('PiCatRing-P', 'PiCatRing-P or (id {} & {})')\n".format(pires_ids, self.protname))
                for a in p.charge_atoms:
                    cmd.select('PosCharge-L', 'PosCharge-L or (id %i & %s)' % (a, self.ligname))
                    log("cmd.select('PosCharge-L', 'PosCharge-L or (id {} & {})')\n".format(a, self.ligname))
            cmd.distance('PiCation', 'ps-picat-1-%i' % i, 'ps-picat-2-%i' % i)
            log("cmd.distance('PiCation', 'ps-picat-1-{0}', 'ps-picat-2-{0}')\n".format(i))
        if self.object_exists('PiCation'):
            cmd.set('dash_color', 'orange', 'PiCation')
            log("cmd.set('dash_color', 'orange', 'PiCation')\n")
            cmd.set('dash_gap', 0.3, 'PiCation')
            log("cmd.set('dash_gap', 0.3, 'PiCation')\n")
            cmd.set('dash_length', 0.6, 'PiCation')
            log("cmd.set('dash_length', 0.6, 'PiCation')\n")

    def show_sbridges(self):
        """Visualize salt bridges."""
        for i, saltb in enumerate(self.plcomplex.saltbridges):
            if saltb.protispos:
                for patom in saltb.positive_atoms:
                    cmd.select('PosCharge-P', 'PosCharge-P or (id %i & %s)' % (patom, self.protname))
                    log("cmd.select('PosCharge-P', 'PosCharge-P or (id {} & {})')\n".format(patom, self.protname))
                for latom in saltb.negative_atoms:
                    cmd.select('NegCharge-L', 'NegCharge-L or (id %i & %s)' % (latom, self.ligname))
                    log("cmd.select('NegCharge-L', 'NegCharge-L or (id {} & {})')\n".format(latom, self.ligname))
                for sbgroup in [['ps-sbl-1-%i' % i, 'Chargecenter-P', saltb.positive_center],
                                ['ps-sbl-2-%i' % i, 'Chargecenter-L', saltb.negative_center]]:
                    cmd.pseudoatom(sbgroup[0], pos=sbgroup[2])
                    log("cmd.pseudoatom('{}', pos={})\n".format(sbgroup[0], sbgroup[2]))
                    cmd.pseudoatom(sbgroup[1], pos=sbgroup[2])
                    log("cmd.pseudoatom('{}', pos={})\n".format(sbgroup[1], sbgroup[2]))
                cmd.distance('Saltbridges', 'ps-sbl-1-%i' % i, 'ps-sbl-2-%i' % i)
                log("cmd.distance('Saltbridges', 'ps-sbl-1-{0}', 'ps-sbl-2-{0}')\n".format(i))
            else:
                for patom in saltb.negative_atoms:
                    cmd.select('NegCharge-P', 'NegCharge-P or (id %i & %s)' % (patom, self.protname))
                    log("cmd.select('NegCharge-P', 'NegCharge-P or (id {} & {})')\n".format(patom, self.protname))
                for latom in saltb.positive_atoms:
                    cmd.select('PosCharge-L', 'PosCharge-L or (id %i & %s)' % (latom, self.ligname))
                    log("cmd.select('PosCharge-L', 'PosCharge-L or (id {} & {})')\n".format(latom, self.ligname))
                for sbgroup in [['ps-sbp-1-%i' % i, 'Chargecenter-P', saltb.negative_center],
                                ['ps-sbp-2-%i' % i, 'Chargecenter-L', saltb.positive_center]]:
                    cmd.pseudoatom(sbgroup[0], pos=sbgroup[2])
                    log("cmd.pseudoatom('{}', pos={})\n".format(sbgroup[0], sbgroup[2]))
                    cmd.pseudoatom(sbgroup[1], pos=sbgroup[2])
                    log("cmd.pseudoatom('{}', pos={})\n".format(sbgroup[1], sbgroup[2]))
                cmd.distance('Saltbridges', 'ps-sbp-1-%i' % i, 'ps-sbp-2-%i' % i)
                log("cmd.distance('Saltbridges', 'ps-sbp-1-{0}', 'ps-sbp-2-{0}')\n".format(i))

        if self.object_exists('Saltbridges'):
            cmd.set('dash_color', 'yellow', 'Saltbridges')
            log("cmd.set('dash_color', 'yellow', 'Saltbridges')\n")
            cmd.set('dash_gap', 0.5, 'Saltbridges')
            log("cmd.set('dash_gap', 0.5, 'Saltbridges')\n")

    def show_wbridges(self):
        """Visualize water bridges."""
        for bridge in self.plcomplex.waterbridges:
            if bridge.protisdon:
                cmd.select('HBondDonor-P', 'HBondDonor-P or (id %i & %s)' % (bridge.don_id, self.protname))
                log("cmd.select('HBondDonor-P', 'HBondDonor-P or (id {} & {})')\n".format(bridge.don_id, self.protname))
                cmd.select('HBondAccept-L', 'HBondAccept-L or (id %i & %s)' % (bridge.acc_id, self.ligname))
                log("cmd.select('HBondAccept-L', 'HBondAccept-L or (id {} & {})')\n".format(bridge.acc_id, self.ligname))
                cmd.select('tmp_don', 'id %i & %s' % (bridge.don_id, self.protname))
                log("cmd.select('tmp_don', 'id {} & {}')\n".format(bridge.don_id, self.protname))
                cmd.select('tmp_acc', 'id %i & %s' % (bridge.acc_id, self.ligname))
                log("cmd.select('tmp_acc', 'id {} & {}')\n".format(bridge.acc_id, self.ligname))
            else:
                cmd.select('HBondDonor-L', 'HBondDonor-L or (id %i & %s)' % (bridge.don_id, self.ligname))
                log("cmd.select('HBondDonor-L', 'HBondDonor-L or (id {} & {})')\n".format(bridge.don_id, self.ligname))
                cmd.select('HBondAccept-P', 'HBondAccept-P or (id %i & %s)' % (bridge.acc_id, self.protname))
                log("cmd.select('HBondAccept-P', 'HBondAccept-P or (id {} & {})')\n".format(bridge.acc_id, self.protname))
                cmd.select('tmp_don', 'id %i & %s' % (bridge.don_id, self.ligname))
                log("cmd.select('tmp_don', 'id {} & {}')\n".format(bridge.don_id, self.ligname))
                cmd.select('tmp_acc', 'id %i & %s' % (bridge.acc_id, self.protname))
                log("cmd.select('tmp_acc', 'id {} & {}')\n".format(bridge.acc_id, self.protname))
            cmd.select('Water', 'Water or (id %i & resn HOH)' % bridge.water_id)
            log("cmd.select('Water', 'Water or (id {} & resn HOH)')\n".format(bridge.water_id))
            cmd.select('tmp_water', 'id %i & resn HOH' % bridge.water_id)
            log("cmd.select('tmp_water', 'id {} & resn HOH')\n".format(bridge.water_id))
            cmd.distance('WaterBridges', 'tmp_acc', 'tmp_water')
            log("cmd.distance('WaterBridges', 'tmp_acc', 'tmp_water')\n")
            cmd.distance('WaterBridges', 'tmp_don', 'tmp_water')
            log("cmd.distance('WaterBridges', 'tmp_don', 'tmp_water')\n")
        if self.object_exists('WaterBridges'):
            cmd.set('dash_color', 'lightblue', 'WaterBridges')
            log("cmd.set('dash_color', 'lightblue', 'WaterBridges')\n")
        cmd.delete('tmp_water or tmp_acc or tmp_don')
        log("cmd.delete('tmp_water or tmp_acc or tmp_don')\n")
        cmd.color('lightblue', 'Water')
        log("cmd.color('lightblue', 'Water')\n")
        cmd.show('spheres', 'Water')
        log("cmd.show('spheres', 'Water')\n")

    def show_metal(self):
        """Visualize metal coordination."""
        metal_complexes = self.plcomplex.metal_complexes
        if not len(metal_complexes) == 0:
            self.select_by_ids('Metal-M', self.metal_ids)
            for metal_complex in metal_complexes:
                cmd.select('tmp_m', 'id %i' % metal_complex.metal_id)
                log("cmd.select('tmp_m', 'id {}')\n".format(metal_complex.metal_id))
                cmd.select('tmp_t', 'id %i' % metal_complex.target_id)
                log("cmd.select('tmp_t', 'id {}')\n".format(metal_complex.target_id))
                if metal_complex.location == 'water':
                    cmd.select('Metal-W', 'Metal-W or id %s' % metal_complex.target_id)
                    log("cmd.select('Metal-W', 'Metal-W or id {}')\n".format(metal_complex.target_id))
                if metal_complex.location.startswith('protein'):
                    cmd.select('tmp_t', 'tmp_t & %s' % self.protname)
                    log("cmd.select('tmp_t', 'tmp_t & {}')\n".format(self.protname))
                    cmd.select('Metal-P', 'Metal-P or (id %s & %s)' % (metal_complex.target_id, self.protname))
                    log("cmd.select('Metal-P', 'Metal-P or (id {} & {})')\n".format(metal_complex.target_id, self.protname))
                if metal_complex.location == 'ligand':
                    cmd.select('tmp_t', 'tmp_t & %s' % self.ligname)
                    log("cmd.select('tmp_t', 'tmp_t & {}')\n".format(self.ligname))
                    cmd.select('Metal-L', 'Metal-L or (id %s & %s)' % (metal_complex.target_id, self.ligname))
                    log("cmd.select('Metal-L', 'Metal-L or (id {} & {})')\n".format(metal_complex.target_id, self.ligname))
                cmd.distance('MetalComplexes', 'tmp_m', 'tmp_t')
                log("cmd.distance('MetalComplexes', 'tmp_m', 'tmp_t')\n")
                cmd.delete('tmp_m or tmp_t')
                log("cmd.delete('tmp_m or tmp_t')\n")
        if self.object_exists('MetalComplexes'):
            cmd.set('dash_color', 'violetpurple', 'MetalComplexes')
            log("cmd.set('dash_color', 'violetpurple', 'MetalComplexes')\n")
            cmd.set('dash_gap', 0.5, 'MetalComplexes')
            log("cmd.set('dash_gap', 0.5, 'MetalComplexes')\n")
            # Show water molecules for metal complexes
            cmd.show('spheres', 'Metal-W')
            log("cmd.show('spheres', 'Metal-W')\n")
            cmd.color('lightblue', 'Metal-W')
            log("cmd.color('lightblue', 'Metal-W')\n")



    def selections_cleanup(self):
        """Cleans up non-used selections"""

        if not len(self.plcomplex.unpaired_hba_idx) == 0:
            self.select_by_ids('Unpaired-HBA', self.plcomplex.unpaired_hba_idx, selection_exists=True)
        if not len(self.plcomplex.unpaired_hbd_idx) == 0:
            self.select_by_ids('Unpaired-HBD', self.plcomplex.unpaired_hbd_idx, selection_exists=True)
        if not len(self.plcomplex.unpaired_hal_idx) == 0:
            self.select_by_ids('Unpaired-HAL', self.plcomplex.unpaired_hal_idx, selection_exists=True)

        selections = cmd.get_names("selections")
        for selection in selections:
            if cmd.count_atoms(selection) == 0:
                cmd.delete(selection)
                log("cmd.delete('{}')\n".format(selection))
        cmd.deselect()
        log("cmd.deselect()\n")
        cmd.delete('tmp*')
        log("cmd.delete('tmp*')\n")
        cmd.delete('ps-*')
        log("cmd.delete('ps-*')\n")

    def selections_group(self):
        """Group all selections"""
        cmd.group('Structures', '%s %s %sCartoon' % (self.protname, self.ligname, self.protname))
        log("cmd.group('Structures', '{0} {1} {0}Cartoon')\n".format(self.protname, self.ligname))
        cmd.group('Interactions', 'Hydrophobic HBonds HalogenBonds WaterBridges PiCation PiStackingP PiStackingT Saltbridges MetalComplexes')
        log("cmd.group('Interactions', 'Hydrophobic HBonds HalogenBonds WaterBridges PiCation PiStackingP PiStackingT Saltbridges MetalComplexes')\n")
        cmd.group('Atoms', '')
        log("cmd.group('Atoms', '')\n")
        cmd.group('Atoms.Protein', 'Hydrophobic-P HBondAccept-P HBondDonor-P HalogenAccept Centroids-P PiCatRing-P StackRings-P PosCharge-P NegCharge-P AllBSRes Chargecenter-P  Metal-P')
        log("cmd.group('Atoms.Protein', 'Hydrophobic-P HBondAccept-P HBondDonor-P HalogenAccept Centroids-P PiCatRing-P StackRings-P PosCharge-P NegCharge-P AllBSRes Chargecenter-P  Metal-P')\n")
        cmd.group('Atoms.Ligand', 'Hydrophobic-L HBondAccept-L HBondDonor-L HalogenDonor Centroids-L NegCharge-L PosCharge-L NegCharge-L ChargeCenter-L StackRings-L PiCatRing-L Metal-L Metal-M Unpaired-HBA Unpaired-HBD Unpaired-HAL Unpaired-RINGS')
        log("cmd.group('Atoms.Ligand', 'Hydrophobic-L HBondAccept-L HBondDonor-L HalogenDonor Centroids-L NegCharge-L PosCharge-L NegCharge-L ChargeCenter-L StackRings-L PiCatRing-L Metal-L Metal-M Unpaired-HBA Unpaired-HBD Unpaired-HAL Unpaired-RINGS')\n")
        cmd.group('Atoms.Other', 'Water Metal-W')
        log("cmd.group('Atoms.Other', 'Water Metal-W')\n")
        cmd.order('*', 'y')
        log("cmd.order('*', 'y')\n")

    def additional_cleanup(self):
        """Cleanup of various representations"""
        cmd.remove('not alt ""+A')  # Remove alternate conformations
        log("cmd.remove('not alt ""+A')  # Remove alternate conformations\n")
        # cmd.hide('labels', 'Interactions')  # Hide labels of lines
        # log("cmd.hide('labels', 'Interactions')  # Hide labels of lines\n")
        cmd.disable('%sCartoon' % self.protname)
        log("cmd.disable('{}Cartoon')\n".format(self.protname))
        cmd.hide('everything', 'hydrogens')
        log("cmd.hide('everything', 'hydrogens')\n")

    def zoom_to_ligand(self):
        """Zoom in too ligand and its interactions."""
        cmd.center(self.ligname)
        log("cmd.center('{}')\n".format(self.ligname))
        cmd.orient(self.ligname)
        log("cmd.orient('{}')\n".format(self.ligname))
        cmd.turn('x', 110)  # If the ligand is aligned with the longest axis, aromatic rings are hidden
        log("cmd.turn('x', 110)  # If the ligand is aligned with the longest axis, aromatic rings are hidden\n")
        if 'AllBSRes' in cmd.get_names("selections"):
            cmd.zoom('%s or AllBSRes' % self.ligname, 3)
            log("cmd.zoom('{} or AllBSRes', 3)\n".format(self.ligname))
        else:
            if self.object_exists(self.ligname):
                cmd.zoom(self.ligname, 3)
                log("cmd.zoom('{}', 3)\n".format(self.ligname))
        cmd.origin(self.ligname)
        log("cmd.origin('{}')\n".format(self.ligname))

    def save_session(self, outfolder, override=None):
        """Saves a PyMOL session file."""
        filename = '%s_%s' % (self.protname.upper(), "_".join([self.hetid, self.plcomplex.chain, self.plcomplex.position]))
        if override is not None:
            filename = override
        cmd.save("/".join([outfolder, "%s.pse" % filename]))
        log("cmd.save('{}.pse')".format(filename))
        write_log("/".join([outfolder, "%s.pml" % filename]))

    def png_workaround(self, filepath, width=1200, height=800):
        """Workaround for (a) severe bug(s) in PyMOL preventing ray-traced images to be produced in command-line mode.
        Use this function in case neither cmd.ray() or cmd.png() work.
        """
        sys.stdout = sys.__stdout__
        cmd.feedback('disable', 'movie', 'everything')
        log("cmd.feedback('disable', 'movie', 'everything')\n")
        cmd.viewport(width, height)
        log("cmd.viewport('{}', '{}')\n".format(width, height))
        cmd.zoom('visible', 1.5)  # Adapt the zoom to the viewport
        log("cmd.zoom('visible', 1.5)  # Adapt the zoom to the viewport\n")
        cmd.set('ray_trace_frames', 1)  # Frames are raytraced before saving an image.
        log("cmd.set('ray_trace_frames', 1)  # Frames are raytraced before saving an image.\n")
        cmd.mpng(filepath, 1, 1)  # Use batch png mode with 1 frame only
        log("cmd.mpng('{}', 1, 1)  # Use batch png mode with 1 frame only\n".format(filepath))
        cmd.mplay()  # cmd.mpng needs the animation to 'run'
        log("cmd.mplay()  # cmd.mpng needs the animation to 'run'\n")
        cmd.refresh()
        log("cmd.refresh()\n")
        originalfile = "".join([filepath, '0001.png'])
        newfile = "".join([filepath, '.png'])

        #################################################
        # Wait for file for max. 1 second and rename it #
        #################################################

        attempts = 0
        while not os.path.isfile(originalfile) and attempts <= 10:
            sleep(0.1)
            attempts += 1
        if os.name == 'nt':  # In Windows, make sure there is no file of the same name, cannot be overwritten as in Unix
            if os.path.isfile(newfile):
                os.remove(newfile)
        os.rename(originalfile, newfile)  # Remove frame number in filename

        #  Check if imagemagick is available and crop + resize the images
        if subprocess.call("type convert", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            attempts, ecode = 0, 1
            # Check if file is truncated and wait if that's the case
            while ecode != 0 and attempts <= 10:
                ecode = subprocess.call(['convert', newfile, '/dev/null'], stdout=open('/dev/null', 'w'),
                                        stderr=subprocess.STDOUT)
                sleep(0.1)
                attempts += 1
            trim = 'convert -trim ' + newfile + ' -bordercolor White -border 20x20 ' + newfile + ';'  # Trim the image
            os.system(trim)
            getwidth = 'w=`convert ' + newfile + ' -ping -format "%w" info:`;'  # Get the width of the new image
            getheight = 'h=`convert ' + newfile + ' -ping -format "%h" info:`;'  # Get the hight of the new image
            newres = 'if [ "$w" -gt "$h" ]; then newr="${w%.*}x$w"; else newr="${h%.*}x$h"; fi;'  # Set quadratic ratio
            quadratic = 'convert ' + newfile + ' -gravity center -extent "$newr" ' + newfile  # Fill with whitespace
            os.system(getwidth + getheight + newres + quadratic)
        else:
            sys.stderr.write('Imagemagick not available. Images will not be resized or cropped.')

    def save_picture(self, outfolder, filename):
        """Saves a picture"""
        self.set_fancy_ray()
        self.png_workaround("/".join([outfolder, filename]))

    def set_fancy_ray(self):
        """Give the molecule a flat, modern look."""
        cmd.set('light_count', 6)
        log("cmd.set('light_count', 6)\n")
        cmd.set('spec_count', 1.5)
        log("cmd.set('spec_count', 1.5)\n")
        cmd.set('shininess', 4)
        log("cmd.set('shininess', 4)\n")
        cmd.set('specular', 0.3)
        log("cmd.set('specular', 0.3)\n")
        cmd.set('reflect', 1.6)
        log("cmd.set('reflect', 1.6)\n")
        cmd.set('ambient', 0)
        log("cmd.set('ambient', 0)\n")
        cmd.set('direct', 0)
        log("cmd.set('direct', 0)\n")
        cmd.set('ray_shadow', 0)  # Gives the molecules a flat, modern look
        log("cmd.set('ray_shadow', 0)  # Gives the molecules a flat, modern look\n")
        cmd.set('ambient_occlusion_mode', 1)
        log("cmd.set('ambient_occlusion_mode', 1)\n")

    def refinements(self):
        """Refinements for the visualization"""

        # Show sticks for all residues interacing with the ligand
        cmd.select('AllBSRes', 'byres (Hydrophobic-P or HBondDonor-P or HBondAccept-P or PosCharge-P or NegCharge-P or StackRings-P or PiCatRing-P or HalogenAcc or Metal-P)')
        log("cmd.select('AllBSRes', 'byres (Hydrophobic-P or HBondDonor-P or HBondAccept-P or PosCharge-P or NegCharge-P or StackRings-P or PiCatRing-P or HalogenAcc or Metal-P)')\n")
        cmd.show('sticks', 'AllBSRes')
        log("cmd.show('sticks', 'AllBSRes')\n")
        cmd.label('AllBSRes and n. ca', 'resn+resi')
        log("cmd.label('AllBSRes and n. ca', 'resn+resi')\n")
        # Show spheres for the ring centroids
        cmd.hide('everything', 'centroids*')
        log("cmd.hide('everything', 'centroids*')\n")
        cmd.show('nb_spheres', 'centroids*')
        log("cmd.show('nb_spheres', 'centroids*')\n")
        # Show spheres for centers of charge
        if self.object_exists('Chargecenter-P') or self.object_exists('Chargecenter-L'):
            cmd.hide('nonbonded', 'chargecenter*')
            log("cmd.hide('nonbonded', 'chargecenter*')\n")
            cmd.show('spheres', 'chargecenter*')
            log("cmd.show('spheres', 'chargecenter*')\n")
            cmd.set('sphere_scale', 0.4, 'chargecenter*')
            log("cmd.set('sphere_scale', 0.4, 'chargecenter*')\n")
            cmd.color('yellow', 'chargecenter*')
            log("cmd.color('yellow', 'chargecenter*')\n")

        cmd.set('valence', 1)  # Show bond valency (e.g. double bonds)
        log("cmd.set('valence', 1)  # Show bond valency (e.g. double bonds)\n")
        # Optional cartoon representation of the protein
        cmd.copy('%sCartoon' % self.protname, self.protname)
        log("cmd.copy('{0}Cartoon', '{0}')\n".format(self.protname))
        cmd.show('cartoon', '%sCartoon' % self.protname)
        log("cmd.show('cartoon', '{}Cartoon')\n".format(self.protname))
        cmd.show('sticks', '%sCartoon' % self.protname)
        log("cmd.show('sticks', '{}Cartoon')\n".format(self.protname))
        cmd.set('stick_transparency', 1, '%sCartoon' % self.protname)
        log("cmd.set('stick_transparency', 1, '{}Cartoon')\n".format(self.protname))

        #if 'PyMOL 1.8.' in get_version_message():
        #    cmd.set('cartoon_transparency', 0.5, '%sCartoon' % self.protname)
        #    log("cmd.set('cartoon_transparency', 0.5, '{}Cartoon')\n".format(self.protname))


        # Resize water molecules. Sometimes they are not heteroatoms HOH, but part of the protein
        cmd.set('sphere_scale', 0.2, 'resn HOH or Water')  # Needs to be done here because of the copy made
        log("cmd.set('sphere_scale', 0.2, 'resn HOH or Water')  # Needs to be done here because of the copy made\n")
        cmd.set('sphere_transparency', 0.4, '!(resn HOH or Water)')
        log("cmd.set('sphere_transparency', 0.4, '!(resn HOH or Water)')\n")

        if 'Centroids*' in cmd.get_names("selections"):
            cmd.color('grey80', 'Centroids*')
            log("cmd.color('grey80', 'Centroids*')\n")
        cmd.hide('spheres', '%sCartoon' % self.protname)
        log("cmd.hide('spheres', '{}Cartoon')\n".format(self.protname))
        cmd.hide('cartoon', '%sCartoon and resn DA+DG+DC+DU+DT+A+G+C+U+T' % self.protname)  # Hide DNA/RNA Cartoon
        log("cmd.hide('cartoon', '{}Cartoon and resn DA+DG+DC+DU+DT+A+G+C+U+T')  # Hide DNA/RNA Cartoon\n".format(self.protname))
        if self.ligname == 'SF4':  # Special case for iron-sulfur clusters, can't be visualized with sticks
            cmd.show('spheres', '%s' % self.ligname)
            log("cmd.show('spheres', '{}')\n".format(self.ligname))

        cmd.hide('everything', 'resn HOH &!Water')  # Hide all non-interacting water molecules
        log("cmd.hide('everything', 'resn HOH &!Water')  # Hide all non-interacting water molecules\n")
        cmd.hide('sticks', '%s and !%s and !AllBSRes' % (self.protname, self.ligname))  # Hide all non-interacting residues
        log("cmd.hide('sticks', '{} and !{} and !AllBSRes')  # Hide all non-interacting residues\n".format(self.protname, self.ligname))
