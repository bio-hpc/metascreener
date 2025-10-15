#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Save all the results of test in cfg.best_score and cfg.plot_data.
# ______________________________________________________________________________________________________________________
import os
import glob
import bisect
from .debug import Debug
from .debug import BColors
from .Ligand import Ligand
from .CreateFingerPrint import CreateFingerPrint
TAG = "ReadData.py"


class ReadData(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.debug = Debug(cfg.mode_debug)
        self.get_data()

    def get_data(self):
        files_json = os.path.join(self.cfg.SHUTTLEMOL_DIRS['folderEnergy'], '*.json')
        files_json = glob.glob(files_json)
        assert files_json
        score_type = None
        data = []
        id_lig = []
        for file_eng in files_json:
            if os.stat(file_eng).st_size != 0:
                pose_lig = Ligand(file_eng, self.cfg)
                if pose_lig != None and pose_lig.get_score() != None:
                    id_lig.append(pose_lig.id_str)
                    data.append(pose_lig.graph_global_score)
                    self.cfg.plot_data.append(pose_lig.get_score())
                    if pose_lig.get_score() > self.cfg.engCorte:
                        if score_type == None or score_type=="positivo":
                            score_type = "positivo"
                            bisect.insort(self.cfg.best_poses, pose_lig)

                    elif pose_lig.get_score() < self.cfg.engCorte:
                        if score_type == None or score_type == "negativo":
                            score_type = "negativo"
                            if self.cfg.opcion in ("VS", "BD", "BDVS", "VSR"):
                                bisect.insort(self.cfg.best_poses, pose_lig)
                    else:
                        print ("Error score equals to threshold " + str(self.cfg.engCorte))

                else:
                    print ("Error global_score in file: remove " + file_eng)
            else:
                print ("Empty file: remove "+file_eng)
                os.remove(file_eng)
        if self.cfg.opcion.startswith("VS"):
            if score_type == "positivo":
                self.cfg.best_poses = reversed(self.cfg.best_poses)
            self.cfg.best_poses = self.cfg.best_poses[:self.cfg.resultados_ficheros+self.cfg.resultados_best_score] 

        # for debug
        for i in self.cfg.best_poses:
            self.debug.show("{}:, {}, {}, {}".format(TAG, i.name, i.get_score(), i.num_execution), BColors.GREEN)  # debug

        prefix_out = os.path.join(self.cfg.OUTPUT_DIRS['workdir'], self.cfg.name_input + "_unclustered_finger_print")
        CreateFingerPrint(self.cfg, data, id_lig, prefix_out)

