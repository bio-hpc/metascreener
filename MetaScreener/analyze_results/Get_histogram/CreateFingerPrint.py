#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Create a matrix with energies in Blind docking
# ______________________________________________________________________________________________________________________


class CreateFingerPrint(object):

    def __init__(self, *args, **kwargs):

        values = [x for x in args]
        if values[0].finger_print:
            if values[0].opcion == "BD":
                if len(args) == 2:
                    cfg = values[0]
                    prefix_out = values[1]
                    scores = []
                    ids = []
                    for i in cfg.best_poses:
                        scores.append(i.graph_global_score)
                        ids.append(i.id_str)
                else:

                    cfg = values[0]
                    scores = values[1]
                    ids = values[2]
                    prefix_out = values[3]
                lig = cfg.best_poses[0]
                cfg.graphicsGenerator.heat_map(lig.graph_global_field, scores, ids,  "ID BD", prefix_out)
                f = open(prefix_out + ".txt", 'w')
                for i in scores:
                    f.write(str(i)[1:-1] + "\n")
                f.close()

