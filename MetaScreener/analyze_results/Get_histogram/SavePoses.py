#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from .debug import Debug
from .debug import BColors


TAG = "SavePoses.py: "
color = BColors.GREEN

class SavePoses(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.debug = Debug(cfg.mode_debug)
        for pose in cfg.best_poses:
            pose.copy_files(self.cfg.OUTPUT_DIRS['bestScore'])
