#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', 'analyze_results', 'Get_histogram'))
from Tools import read_coords, get_rmsd, get_aligned_rmsd


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        lig_original = sys.argv[1]
        lig_dock = sys.argv[2]

        mol1_coords = read_coords(lig_original)
        mol2_coords = read_coords(lig_dock)

        print("RMSD Formula: {:.2f}".format(round(get_rmsd(mol1_coords, mol2_coords), 2)))

        [t, z, r, rmsd, rmsd_svd] = get_aligned_rmsd(mol1_coords, mol2_coords)
        print("RMSD Pymol: {:.2f}".format(round(rmsd, 2)))
        print("RMSD SVD: {:.2f}".format(round(rmsd_svd, 2)))
