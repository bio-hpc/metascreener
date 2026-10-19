#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#   Description: Packs a MetaScreener experiment folder into <experiment>.tar.gz in the current directory,
#                skipping the same job/scratch folders as analyze_results/Get_histogram/ResultPacker.py
# ______________________________________________________________________________________________________________________
import os
import sys
import glob
import tarfile

EXCLUDED_DIRS = ('jobs', 'jobs_out', 'jobs_done', 'grids', 'soft_out')


def pack_experiment(directory):
    directory = os.path.realpath(directory)
    pack_file = os.path.realpath(os.path.basename(directory) + '.tar.gz')
    if os.path.isfile(pack_file):
        os.unlink(pack_file)

    excluded = set(os.path.join(directory, d) for d in EXCLUDED_DIRS)
    tmp_file = pack_file + '.tmp'
    with tarfile.open(tmp_file, 'w:gz') as tgz:
        for item in sorted(glob.glob(os.path.join(directory, '*'))):
            if item in excluded or item.endswith('.tar.gz'):
                continue
            tgz.add(os.path.relpath(item, '.'))
    os.rename(tmp_file, pack_file)
    return pack_file


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python pack_experiment.py experiment_directory")
        sys.exit(1)
    pack_experiment(sys.argv[1])
