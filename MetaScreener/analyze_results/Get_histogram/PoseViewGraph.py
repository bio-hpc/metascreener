#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import re
from .Tools import *
from .debug import BColors

TAG = "PoseViewGrap.py :"
color = BColors.GREEN
EXT_LIG_POSEVIEW = ".mol2"


class PoseviewGraph(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.generate_poseview()

    def generate_poseview(self):
        for lig in self.cfg.best_poses:
            self.run_poseview(lig)

    def run_poseview(self, pose):
        lig_name = os.path.join(self.cfg.OUTPUT_DIRS['bestScore'], pose.file_name + pose.ligand_ext)
        posvw_name = os.path.join(self.cfg.OUTPUT_DIRS['interacciones'], pose.file_name)

        name_aux = pose.file_ori_target
        if bool(self.cfg.file_target_pdb and not self.cfg.file_target_pdb.isspace()):
            name_aux = self.cfg.file_target_pdb
        name_pose, ext_pose = os.path.splitext(pose.file_ori_target)
        for format_out in ['svg', 'png']:
            cmd = '{} {} {} {} {}'.format(
                self.cfg.python_exe,
                self.cfg.ligand_poseview,
                name_aux,
                lig_name,
                posvw_name + "_." + format_out
            )
            print(self.cfg.execute("PoseviewGrpah.py", cmd))
