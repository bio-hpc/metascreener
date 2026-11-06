#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Toy check of the per-task tar index, without running a docking."""
from __future__ import print_function

import glob
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORE = os.path.join(ROOT, 'MetaScreener', 'analyze_results', 'Get_histogram')
sys.path.insert(0, STORE)
import PackedStore  # noqa: E402


def write_pose(stage, ligand, score):
    energies = os.path.join(stage, 'energies')
    molecules = os.path.join(stage, 'molecules')
    soft_out = os.path.join(stage, 'soft_out')
    for path in (energies, molecules, soft_out, os.path.join(stage, 'output')):
        if not os.path.isdir(path):
            os.makedirs(path)
    stem = 'VS_AD_1le0_%s_0_0_0' % ligand
    data = {
        'global_score': str(score),
        'global_score_md': '',
        'global_score_qu': '',
        'coords': ['1', '2', '3'],
        'num_execution': '-1',
        'file_ori_query': 'tar_ligs/%s.pdbqt' % ligand,
        'name': 'tar_ligs',
    }
    with open(os.path.join(energies, stem + '.json'), 'w') as handle:
        json.dump(data, handle)
    with open(os.path.join(molecules, stem + '.pdbqt'), 'w') as handle:
        handle.write('pose %s\n' % ligand)
    with open(os.path.join(soft_out, stem + '.ucm'), 'w') as handle:
        handle.write('log\n')
    return ligand + '.pdbqt'


def pack_task(stage, archive):
    if not os.path.isdir(os.path.dirname(archive)):
        os.makedirs(os.path.dirname(archive))
    tar = tarfile.open(archive, 'w')
    try:
        for name in ('index.jsonl', 'failed.jsonl', 'molecules', 'energies', 'soft_out', 'output'):
            path = os.path.join(stage, name)
            if os.path.exists(path):
                tar.add(path, arcname=name)
    finally:
        tar.close()


def main():
    work = tempfile.mkdtemp(prefix='ms_packed_')
    try:
        experiment = os.path.join(work, 'exp')
        os.makedirs(os.path.join(experiment, 'packed'))
        groups = [
            ('task_00000', [('LIG_a', -1.0), ('LIG_b', -5.0)]),
            ('task_00002', [('LIG_c', -3.0), ('LIG_d', -2.0)]),
        ]
        manifest = []
        for task_name, poses in groups:
            stage = os.path.join(work, task_name)
            os.makedirs(stage)
            listed = []
            for ligand, score in poses:
                listed.append(write_pose(stage, ligand, score))
                manifest.append(listed[-1])
            list_path = os.path.join(stage, 'list')
            with open(list_path, 'w') as handle:
                handle.write('\n'.join(listed) + '\n')
            rc = PackedStore.build_index(
                os.path.join(stage, 'energies'),
                os.path.join(stage, 'index.jsonl'),
                list_path)
            assert rc == 0, rc
            pack_task(stage, os.path.join(experiment, 'packed', task_name + '.tar'))

        with open(os.path.join(experiment, 'ligands.list'), 'w') as handle:
            handle.write('\n'.join(manifest) + '\n')
        with open(os.path.join(experiment, 'packed', 'expected_tasks'), 'w') as handle:
            handle.write('2\n')

        # A ligand without a score is recorded; the task index still succeeds.
        bad = os.path.join(work, 'bad')
        os.makedirs(os.path.join(bad, 'energies'))
        write_pose(bad, 'ONLY', -4.0)
        with open(os.path.join(bad, 'list'), 'w') as handle:
            handle.write('ONLY.pdbqt\nMISSING.pdbqt\n')
        rc = PackedStore.build_index(
            os.path.join(bad, 'energies'),
            os.path.join(bad, 'index.jsonl'),
            os.path.join(bad, 'list'))
        assert rc == 0, rc
        failed_names = [
            json.loads(line)['ligand']
            for line in open(os.path.join(bad, 'failed.jsonl')) if line.strip()]
        assert failed_names == ['MISSING.pdbqt'], failed_names
        # 1 of 4 is 25%, above the 5% limit.
        assert PackedStore.assess_coverage(experiment)[0] == 'ok'
        too_many = os.path.join(work, 'too_many')
        os.makedirs(os.path.join(too_many, 'packed'))
        with open(os.path.join(too_many, 'ligands.list'), 'w') as handle:
            handle.write('A.pdbqt\nB.pdbqt\nC.pdbqt\nD.pdbqt\n')
        stage = os.path.join(work, 'too_stage')
        os.makedirs(os.path.join(stage, 'energies'))
        write_pose(stage, 'A', -1.0)
        write_pose(stage, 'B', -2.0)
        write_pose(stage, 'C', -3.0)
        with open(os.path.join(stage, 'list'), 'w') as handle:
            handle.write('A.pdbqt\nB.pdbqt\nC.pdbqt\nD.pdbqt\n')
        assert PackedStore.build_index(
            os.path.join(stage, 'energies'),
            os.path.join(stage, 'index.jsonl'),
            os.path.join(stage, 'list')) == 0
        pack_task(stage, os.path.join(too_many, 'packed', 'task_00000.tar'))
        assert PackedStore.assess_coverage(too_many)[0] == 'too_many'
        # 1 of 4 is exactly 25%, which -mf 25 accepts. 24 does not.
        assert PackedStore.assess_coverage(too_many, 25)[0] == 'ok'
        assert PackedStore.assess_coverage(too_many, 24)[0] == 'too_many'
        try:
            PackedStore.failure_percent(101)
        except SystemExit:
            pass
        else:
            raise AssertionError('101 must be rejected')

        assert PackedStore.materialize(experiment, 1, 1, 0.0) == 0
        scores = open(os.path.join(experiment, 'packed', 'all_scores.txt')).read().split()
        assert len(scores) == 4, scores
        jsons = sorted(glob.glob(os.path.join(experiment, 'energies', '*.json')))
        mols = sorted(glob.glob(os.path.join(experiment, 'molecules', '*.pdbqt')))
        assert len(jsons) == 2, jsons
        assert len(mols) == 2, mols
        kept = set(os.path.basename(path) for path in mols)
        assert kept == set([
            'VS_AD_1le0_LIG_b_0_0_0.pdbqt',
            'VS_AD_1le0_LIG_c_0_0_0.pdbqt',
        ]), kept
        assert PackedStore.write_scoring_csv(experiment) == 0
        lines = open(os.path.join(experiment, 'Results_scoring.csv')).read().splitlines()
        assert lines[0].startswith('Global score;')
        assert len(lines) == 5, lines
        assert lines[1].startswith('-5.0;') or lines[1].startswith('-5;'), lines[1]
        print('packed store ok (%s)' % sys.version.split()[0])
    finally:
        shutil.rmtree(work)


if __name__ == '__main__':
    main()
