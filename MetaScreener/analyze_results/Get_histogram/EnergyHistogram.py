#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Generate energy plots
# ______________________________________________________________________________________________________________________
from .Tools import *


class EnergyHistogram(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.generate_histograms()
        self.gorup_global_energy()

    def generate_histograms(self):

        for lig in self.cfg.best_poses:
            cmd = '{} {} {} {} {} {} {}'.format(self.cfg.python_exe, self.cfg.graph_energies, lig.file_json , self.cfg.OUTPUT_DIRS['afinidades'],
                                     self.cfg.interactions_global, self.cfg.interactions_atoms, self.cfg.heat_map_interactions)
            self.cfg.execute("generate_graphs", cmd)

    def gorup_global_energy(self):
        scores = []
        name_ligs = []
        for i in self.cfg.best_poses:
            scores.append(i.graph_global_score)
            name_ligs.append(i.file_name)
        lig = self.cfg.best_poses[0]
        out_put = os.path.join(self.cfg.OUTPUT_DIRS['bestScore'], self.cfg.OUTPUT_GRAPHS['grap10']['outPut'])
        self.cfg.graphicsGenerator.generate_best_pose_join_graph(lig.graph_global_field, scores, name_ligs,
                                                              lig.graph_global_color,  out_put)
