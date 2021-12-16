#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from .Tools import *
from .debug import BColors
TAG = "EnergyHistogram.py: "
color = BColors.GREEN


class JoinImages (object):
    TAG = "JoinImages.py"

    def __init__(self, cfg):
        self.cfg = cfg
        self.merge_imgs()

    def merge_imgs(self):
        for query in self.cfg.best_poses:

            if query.file_name.startswith('VS') or '_BD' in query.file_name:

                salida_pack = self.cfg.OUTPUT_DIRS['afinidades'] + '/' + query.file_name + "_pack.png"
                imagen_a = self.cfg.OUTPUT_DIRS['afinidades'] + '/' + query.file_name + "_global.png"
                imagen_b = self.cfg.OUTPUT_DIRS['interacciones'] + '/' + query.file_name + ""
                imagen_c = self.cfg.OUTPUT_DIRS['afinidades'] + '/' + query.file_name + "_atom.png"
                imagen_d = self.cfg.OUTPUT_DIRS['interacciones'] + '/' + query.file_name + "_povw_hist.png"
                try:

                    cmd="montage -mode concatenate -tile 2x{} -geometry 800x600 {} {} {} {} {} ".format(
                            2 if os.path.isfile(imagen_b +"."+ self.cfg.format_graph) else 1,
                            imagen_a if os.path.exists(imagen_a) else '',
                            imagen_c if os.path.exists(imagen_c) else '',
                            imagen_b+"_pdb.png" if os.path.exists(imagen_b+"_pdb.png") else '',
                            imagen_d if os.path.exists(imagen_d) else '',
                            salida_pack
                        )

                    self.cfg.execute(TAG, cmd)
                except Exception:
                    print("Error: joining images "+salida_pack)

