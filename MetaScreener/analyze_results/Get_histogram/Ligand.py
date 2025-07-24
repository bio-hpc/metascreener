#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function, \
    unicode_literals
import six
import re
import json
import pybel
from .Tools import *


#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Holds all ligand data
# 
#   'coords': [u'0.385', u'1.778', u'6.863'],
#   'file': u'queries/test/GLA.pdbqt',
#   'file_result': "/home/j...tleMol/BD_AD_1le0_GLA_2018-07-11/molecules/2-BD_AD_1le0_GLA_-4.545_2.171_0.623.pdbqt"
#   'global_score': u'-3.97811',
#   'global_score_md': u'-3.97811',
#   'grap_atom_color': ['b', 'g', ..],
#   'grap_atom_filed': [u'Gauss1',u'Gauss2',...],
#   'grap_atom_score': [['1.052', '17.77', ...], ['5', '12.0', ...]],
#   'grap_global_color': ['b', 'g', ...],
#   'grap_global_filed': ['Gauss1','Gauss2',...],
#   'grap_global_score': ['-1.86712','-1.25704'...]
#   'name': 'GLA',
#   'num_aminoacid': '1',
#   'num_execution': '0-'
# ______________________________________________________________________________________________________________________


class Ligand(object):
    TOLERANCIA = 0.1
    FLEX_DIR_RE = re.compile(r'/\d+-.+_([A-Z]+)_(\d+)/?$', re.I)
    TAG = "ReadLigand.py"

    def __init__(self, fname, cfg, score_field=None, score_ascending=True):
        """
        Initialize Ligand object with optional custom scoring parameters.
        
        Args:
            fname: Path to JSON file with ligand data
            cfg: Configuration object
            score_field: Optional field name to use for scoring (string)
            score_ascending: Optional sort order flag (boolean, default True for lower is better)
        """
        self.overlap_cmd = cfg.external_sw_folder + "/overlap/overlap {} {} | grep -i volume | tail -1 |awk '{{print $2}}'"
        self.cfg = cfg
        self._volume = None
        self._mol_coords = None
        self._center = None
        
        # Store custom scoring parameters
        self.score_field = score_field
        self.score_ascending = score_ascending

        for key, value in six.iteritems(read_json(fname, cfg)):
            setattr(self, key, value)

        self.file_json = fname
        self.id_str = str(self.num_execution) + "-"
        self.ligand_ext = os.path.splitext(self.file_result)[1]
        self.dir_name, self.basename = os.path.split(fname)
        self.file_name, _ = os.path.splitext(self.basename)

    def get_score(self):
        """
        Get the score for this ligand using priority hierarchy or custom field.
        
        Returns:
            float: The score value
            
        Raises:
            ValueError: If custom score_field is specified but doesn't exist
        """
        # If custom score field is specified, use it
        if self.score_field is not None:
            score_value = self._get_custom_score()
            if score_value is not None:
                return score_value
            else:
                raise ValueError("Score field '{}' not found in ligand data. Available fields: {}".format(
                    self.score_field, self._get_available_score_fields()))
        
        # Default hierarchy for standard scoring
        if hasattr(self, "global_score_qu") and getattr(self, "global_score_qu") and "global_score_qu" != "":
            return float(getattr(self, "global_score_qu"))
        elif hasattr(self, "global_score_md") and getattr(self, "global_score_md") and "global_score_md" != "":
            return float(getattr(self, "global_score_md"))
        elif hasattr(self, 'global_score') and self.global_score != "" and hasattr(self, 'graph_global_score'):
            return float(self.global_score)
        return None

    def _get_custom_score(self):
        """
        Get score from custom field.
        
        Returns:
            float or None: Score value if field exists and is valid, None otherwise
        """
        # Direct field access for main score fields
        main_fields = ['global_score', 'global_score_md', 'global_score_qu', 
                      'CNNscore', 'CNNAffinity', 'CNN_VS']
        
        if self.score_field in main_fields:
            if hasattr(self, self.score_field):
                value = getattr(self, self.score_field)
                if value is not None and value != "":
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return None
            return None
        
        # Check graph_global_score fields for extended scoring
        if hasattr(self, 'graph_global_field') and hasattr(self, 'graph_global_score'):
            try:
                field_index = self.graph_global_field.index(self.score_field)
                score_value = self.graph_global_score[field_index]
                return float(score_value)
            except (ValueError, IndexError, TypeError):
                return None
        
        return None

    def _get_available_score_fields(self):
        """
        Get list of available score fields for error reporting.
        
        Returns:
            list: Available field names
        """
        available_fields = []
        
        # Main score fields
        main_fields = ['global_score', 'global_score_md', 'global_score_qu', 
                      'CNNscore', 'CNNAffinity', 'CNN_VS']
        
        for field in main_fields:
            if hasattr(self, field) and getattr(self, field) not in [None, ""]:
                available_fields.append(field)
        
        # Graph fields
        if hasattr(self, 'graph_global_field'):
            available_fields.extend(self.graph_global_field)
        
        return available_fields

    def __lt__(self, other):
        """
        Compare ligands based on score with configurable sort order.
        
        Args:
            other: Another Ligand object
            
        Returns:
            bool: True if this ligand should be ranked higher
        """
        self_score = self.get_score()
        other_score = other.get_score()
        
        if self_score is None or other_score is None:
            return False
            
        # Use score_ascending flag to determine comparison direction
        if self.score_ascending:
            return self_score < other_score  # Lower is better
        else:
            return self_score > other_score  # Higher is better

    def check_overlap(self, other):
        return self.get_volumen(other) < self.volume + other.volume - Ligand.TOLERANCIA

    @property
    def volume(self):
        if self._volume is None:
            self._volume = self.get_volumen()
        return self._volume

    @property
    def mol_coords(self):
        pybel.ob.obErrorLog.StopLogging()
        if self._mol_coords is None:
            mols = [mol for mol in pybel.readfile(str(self.ligand_ext.strip('.')), str(self.file_result))]
            assert len(mols) == 1
            self._mol_coords = tuple(np.array(atom.coords) for atom in mols[0] if not atom.OBAtom.IsHydrogen())
        return self._mol_coords

    def get_volumen(self, other=None):
        cmd = self.overlap_cmd.format(
            self.file_result,
            other.file_result if other else ''
        )
        ret = subprocess.check_output(cmd, shell=True, preexec_fn=init_worker)
        return float(ret)

    def copy_files(self, target_dir):
        reasign_charges = "python " + self.cfg.extra_metascreener + "/reasign_charges.py {} {}"
        if self.num_execution != -1:
            pattern = '{}*{}[!0-9]*'.format(self.cfg.opcion, self.name)
            pattern = '{}_'.format(self.num_execution) + pattern
        else:
            pattern = "{}.*".format(self.file_name)

        dirs = set((self.cfg.SHUTTLEMOL_DIRS[k] for k in ('folderMolec', 'folderEnergy')))
        for folder in dirs:
            cp_pattern(folder, pattern, target_dir, self.cfg)

        if self.cfg.programa.startswith("LF"):
            if self.cfg.opcion.startswith("VS"):
                for filename in os.listdir(self.cfg.file_query):
                    if self.ligand_ext in filename and "_"+os.path.splitext(filename)[0]+"_" in self.file_name:
                        cmd = reasign_charges.format(
                            self.cfg.file_query + "/" + filename,
                            target_dir + self.file_name + self.ligand_ext
                        )
            else:
                cmd = reasign_charges.format(
                    self.cfg.file_query,
                    target_dir + self.file_name + self.ligand_ext
                )  
            subprocess.check_output(cmd, shell=True)

