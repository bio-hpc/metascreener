#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Save the results in Virtual Screening
# ______________________________________________________________________________________________________________________
from .Tools import *


class SaveResults(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.count_best_score = 0
        self.cp_protein()
        self.save_vs_results()

    def cp_protein(self):
        cp_file(self.cfg.file_target, self.cfg.cpy_file_target, self.cfg)
        for pose in self.cfg.best_poses:
            pose.file_ori_target = self.cfg.cpy_file_target

    def cp_vsr_target(self):
        if self.cfg.opcion.startswith("VSR"):
            for pose in self.cfg.best_poses:
                end_target_file = os.path.join(self.cfg.OUTPUT_DIRS['bestScore'] +os.path.basename(pose.file_ori_target))
                cp_file(pose.file_ori_target, end_target_file, self.cfg)
                pose.file_ori_target = end_target_file

    def save_vs_results(self):
        if self.cfg.opcion.startswith("VS"):
            for pose in self.cfg.best_poses:
                if self.count_best_score < self.cfg.resultados_best_score:
                    rute_tmp = self.cfg.OUTPUT_DIRS['bestScore']
                else:
                    rute_tmp = self.cfg.OUTPUT_DIRS['nextBestScore']
                pose.copy_files(rute_tmp)
                self.count_best_score += 1
            self.cfg.best_poses = self.cfg.best_poses[:self.cfg.resultados_best_score]
        self.cp_vsr_target()
