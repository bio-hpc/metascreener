#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
import glob
import math
import shutil
import signal
import progressbar
import subprocess
import json
import pybel
import numpy as np
from debug import BColors


def custom_pbar(fd=sys.stdout, *args, **kwargs):
    pbar_fmt = [
        progressbar.FormatLabel(' %(value)d / %(max)s '),
        progressbar.Bar(),
        ' [', progressbar.Timer(), ']', ' (', progressbar.ETA(), ') ',
    ]
    return progressbar.ProgressBar(widgets=pbar_fmt, fd=fd, *args, **kwargs)


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def cp_pattern(folder, pattern, tgt, cfg):
    for f in glob.glob(os.path.join(folder, pattern)):
        cfg.debug.show("TOOLS" + " cp " + os.path.join(folder, pattern) + " " + tgt, BColors.GREEN)
        shutil.copy(f, tgt)


def cp_file(file_source, file_out, cfg):
    cfg.debug.show("TOOLS" + " cp " + file_source + " " + file_out, BColors.GREEN)
    shutil.copy(file_source, file_out)


def find_file(pattern):
    files = glob.glob(pattern)
    assert len(files) == 1
    return files[0]


def read_coords(fname, cfg):
    cmd = "{} {}{} {} {}".format(cfg.python_exe, cfg.extra_metascreener, "standar_file_coords.py", fname," |grep -v \"#\"")
    lst_aux = str(cfg.execute("tools.py", cmd)).split("\n")

    lst_coords = []
    for i in lst_aux:
        if not i.startswith("#") and i != "":
            aux = i.split(":")
            if len(aux) >= 3:
               lst_coords.append([float(aux[0]), float(aux[1]), float(aux[2])])
    return lst_coords

def read_coords(fname, all_atoms=False):
    mol = read_molecule(fname)
    return np.array([np.array(atm.coords) for atm in mol.atoms if all_atoms or not atm.OBAtom.IsHydrogen()])

def read_molecule(fname):
    pybel.ob.obErrorLog.StopLogging()
    file_name, file_ext = os.path.splitext(fname)
    mols = [mol for mol in pybel.readfile(str(file_ext.strip('.')), str(fname))]
    assert len(mols) == 1
    return mols[0]

def get_center_ligand(fname, cfg):
    coords = read_coords(fname, cfg)
    x = y = z = 0
    for i in coords:
        x += i[0]
        y += i[1]
        z += i[2]
    res = (x / len(coords)) + (y / len(coords)) + (z / len(coords))
    return res


def get_sq_dist(point1, point2):
    return np.sqrt(np.power((point1 - point2), 2))


def get_dist(point1, point2):
    return np.sqrt(get_sq_dist(point1, point2))


def get_rmsd(coords1, coords2):
    dist = sum(get_sq_dist(atomA, atomB) for (atomA, atomB) in zip(coords1, coords2))
    return np.sqrt(dist / float(len(coords1)))


def get_aligned_rmsd(target_array, source_array):
    """
    fit(target_array, source_array) -> (t1, t2, rot_mtx, rmsd) [fit_result]

    Calculates the translation vectors and rotation matrix required
    to superimpose source_array onto target_array.  Original arrays are
    not modified.  NOTE: Currently assumes 3-dimensional coordinates

    t1,t2 are vectors from origin to centers of mass...
    """

    if len(target_array) != len(source_array):
        print("Error: arrays must be of same length for RMS fitting.")
        print("target_array: " + str(target_array))
        print("source_array: " + str(source_array))
        raise ValueError
    if len(target_array[0]) != 3 or len(source_array[0]) != 3:
        print("Error: arrays must be dimension 3 for RMS fitting.")
        raise ValueError
    nvec = len(target_array)
    ndim = 3
    maxiter = 2000
    tol = 0.001

    # Calculate translation vectors (center-of-mass).
    t1 = sum(target_array) / len(target_array)
    t2 = sum(source_array) / len(source_array)

    vt1 = target_array - t1
    vt2 = source_array - t2

    # Calculate correlation matrix.
    corr_mtx = np.dot(np.transpose(vt2), vt1)
    rot_mtx = np.eye(3)

    u, s, vt = np.linalg.svd(corr_mtx)
    rot_svd = np.dot(u, np.dot(np.diag([1, 1, np.linalg.det(np.dot(u, vt))]), vt))

    vt3 = np.inner(vt2, rot_svd.T)

    rmsd_vsd = sum(get_sq_dist(vt1, vt3))
    rmsd_vsd = np.sqrt(rmsd_vsd / nvec)

    # Main iteration scheme (hardwired for 3X3 matrix, but could be extended).
    iters = 0
    while iters < maxiter:
        iters += 1
        iy = iters % ndim
        iz = (iters + 1) % ndim
        sig = corr_mtx[iz][iy] - corr_mtx[iy][iz]
        gam = corr_mtx[iy][iy] + corr_mtx[iz][iz]

        sg = (sig ** 2 + gam ** 2) ** 0.5
        if sg != 0.0 and (abs(sig) > tol * abs(gam)):
            sg = 1.0 / sg
            bb = gam * corr_mtx[iy] + sig * corr_mtx[iz]
            cc = gam * corr_mtx[iz] - sig * corr_mtx[iy]
            corr_mtx[iy] = bb * sg
            corr_mtx[iz] = cc * sg

            bb = gam * rot_mtx[iy] + sig * rot_mtx[iz]
            cc = gam * rot_mtx[iz] - sig * rot_mtx[iy]
            rot_mtx[iy] = bb * sg
            rot_mtx[iz] = cc * sg

        else:
            # We have a converged rotation matrix.  Calculate RMS deviation.
            vt3 = np.inner(vt2, rot_mtx)

            _rmsd = sum(get_sq_dist(vt1, vt3))
            _rmsd = np.sqrt(_rmsd / nvec)
            return t1, t2, rot_mtx, _rmsd, rmsd_vsd

    # Too many iterations; something wrong.
    print("Error: Too many iterations in RMS fit.")
    return -1., -1., np.array((3, 3)), -1., rmsd_vsd


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def convert_molecule(fnames, out_path, cfg):
    cmd = '{} {} {} {} -b 2> /dev/null'.format(cfg.python_exe, cfg.convert_to, fnames, out_path)
    cfg.execute("Tools.py", cmd)


def read_json(fname, cfg=None):
    obj = {}
    try:
        with open(fname) as f_json:
            data = json.load(f_json)

            for k, v in data.items():
                if (k) == "name":
                    obj[k] = v
                elif k == "num_execution":
                    obj[k] = int(v)
                elif type(v) != list and is_number(v):
                    obj[k] = float(v)
                elif (k) == "coords":
                    obj[k] = [float(i) for i in v]
                elif (k) == "graph_global_score":
                    obj[k] = [float(i) for i in v]

                elif (k) == "graph_atoms_score":
                    for row in range(len(v)):
                        v[row] = [float(i) for i in v[row]]
                        obj[k] = v
                else:
                    obj[k] = v

    except Exception as e:
        if not cfg:
            cfg.print_error("Ligand.py ", str(e))
            cfg.print_error("Ligand.py ", "ERROR: Bad json File  " + fname)
        else:
            print("ERROR: " + str(e))
            print("ERROR: Bad json File  " + fname)
    return obj
