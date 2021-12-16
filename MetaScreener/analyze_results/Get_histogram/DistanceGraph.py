#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from .Tools import *


class DistanceGraph(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.generate_dist_graph()

    def generate_dist_graph(self):
        nom_lig = []      # ligand
        points_lig = []   # x + y + z


        for fich in self.cfg.best_poses:
            lig_center = get_center_ligand(fich.file_result, self.cfg)
            points_lig.append(lig_center)

        count_lig = len(points_lig) - 1
        data = np.zeros((count_lig, count_lig))

        nom_lig.append('Cl.{}'.format(1))
        for i in range(1, len(points_lig)):
            nom_lig.append('Cl.{}'.format(i + 1))
            for j in range(i):
                data[i - 1][j] = get_dist(points_lig[i], points_lig[j])
        out_put = os.path.join(self.cfg.file_input, self.cfg.name_input + '_Cluster_Distances_Plot')
        self.cfg.graphicsGenerator.generate_distance_graph(data, nom_lig, count_lig, out_put)

