#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess

from .debug import Debug
from .debug import BColors

lvlDebug = 10
color = BColors.GREEN

SCRIPT_MUTACION = "scriptsGeneracionResultados/graficasEnergia/scriptGeneraGraficaMutacion.py"


class MutacionGraphs(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.debug = Debug(self.cfg.mode_debug)
        self.generate_graph()

    def generate_graph(self):
        comando = (self.cfg.python_exe, SCRIPT_MUTACION, self.cfg.fileEntrada, self.cfg.extProteina,
                   self.cfg.fileLigando)
        self.debug.show(' '.join(comando), color, lvlDebug)
        ret = subprocess.check_output(comando)
        print(ret)







