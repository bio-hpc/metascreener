#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez@ucam.edu
#   Description: Generates a global histogram with all test data
# ______________________________________________________________________________________________________________________


class GlobalHistogram(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.generate_histogram()
 
    def generate_histogram(self):

        self.cfg.graphicsGenerator.generate_histogram(self.cfg.plot_data, self.cfg.OUTPUT_GRAPHS['histogram']['title'],
                                             'Binding energy (kcal/mol)', 'Frequency', 'symlog', 0,
                                             self.cfg.OUTPUT_GRAPHS['histogram']['outPut'],)
