#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess
import re
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from .Tools import *
from .debug import BColors

TAG = "plipGraph.py :"
color = BColors.GREEN


class PlipGraph(object):

    def __init__(self, cfg ):
        self.cfg = cfg
        self.best_poses = self.cfg.best_poses
        self.generate_plip()

    def generate_plip(self):
        for pose in self.best_poses:
            prefix_out = os.path.join(self.cfg.OUTPUT_DIRS['interacciones'], pose.file_name)
            prefix_poses = prefix_out.replace("clustered_interactions/", "clustered_poses/")
            if bool(self.cfg.file_target_pdb and not self.cfg.file_target_pdb.isspace()) :
                cmd = '{} {} {} {} {} {}'.format(
                    self.cfg.python_exe,
                    self.cfg.ligand_plip,
                    pose.file_ori_target,
                    prefix_poses+".pdbqt",
                    prefix_out,
                    self.cfg.file_target_pdb
                )
            else:
                cmd = '{} {} {} {} {}'.format(
                    self.cfg.python_exe,
                    self.cfg.ligand_plip,
                    pose.file_ori_target,
                    prefix_poses+".pdbqt",
                    prefix_out,       
                )
            print(cmd)
            self.cfg.execute("Plip Interactions", cmd)
