#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import glob
import shutil
import tarfile
from .debug import Debug
from .debug import BColors

TAG = "Packing: "
lvlDebug = 10
color = BColors.GREEN


class ResultPacker(object):

    def __init__(self, cfg):
        self.readme_file = cfg.extra_metascreener+'/README.txt'
        self.cfg = cfg
        self.debug = Debug(self.cfg.mode_debug)

        self.pack_file = os.path.realpath(os.path.join(self.cfg.file_input, self.cfg.name_input + '.tar.gz'))
        self.pack()

    def pack(self):
        self.delete_tar_gz()
        self.cp_summary()
        self.cp_resume()

        with tarfile.open(self.pack_file, 'w:gz') as tgz:
            for item in glob.glob(os.path.join(self.cfg.OUTPUT_DIRS['workdir'], '*')):
                if item != self.pack_file and item not in {
                    self.cfg.SHUTTLEMOL_DIRS['folderErrorJob'],
                    self.cfg.SHUTTLEMOL_DIRS['folderOutJob'],
                    self.cfg.SHUTTLEMOL_DIRS['folderTemplatesJobs'],
                    self.cfg.SHUTTLEMOL_DIRS['folderJobsDone'],
                    self.cfg.SHUTTLEMOL_DIRS['folderGrid'],
                    self.cfg.SHUTTLEMOL_DIRS['folderOutUcm'],
                }:
                    if not self.cfg.resume and "/Resume" in item:
                        pass
                    else:
                        tgz.add(os.path.relpath(item, '.'))

            results_csv = os.path.join(self.cfg.file_input, 'Results_scoring.csv')
            if os.path.isfile(results_csv):
                tgz.add(os.path.relpath(results_csv, '.'))

        tgt_file = os.path.realpath(os.path.basename(self.pack_file))
        if os.path.isfile(tgt_file):
            os.unlink(tgt_file)
        shutil.move(self.pack_file, tgt_file)

    def cp_resume(self):
        if self.cfg.resume and self.cfg.OUTPUT_DIRS['interacciones'] == self.cfg.OUTPUT_DIRS['afinidades']:

            for file in glob.glob(self.cfg.file_input+"/Resume*"):
              shutil.copy(file, self.cfg.OUTPUT_DIRS['bestScore'])

    def cp_summary(self):
        if self.cfg.copy_summary:
            shutil.copy(self.readme_file, self.cfg.file_input)

    def delete_tar_gz(self):
        if os.path.isfile(self.pack_file):
            os.unlink(self.pack_file)

if __name__ == '__main__':
    pass
