#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One tar per VS task, plus the index the histogram and the CSV read.

Python 2.7 (inside the Singularity image) and Python 3 (on the host).
"""
from __future__ import print_function

import argparse
import glob
import heapq
import json
import os
import shutil
import sys
import tarfile


def _text(line):
    if not isinstance(line, str):
        return line.decode('utf-8')
    return line


def effective_score(record):
    """Same priority as Ligand.get_score, but a real 0 is a score."""
    for key in ('global_score_qu', 'global_score_md', 'global_score'):
        value = record.get(key)
        if value is None or value == '':
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def ligand_basename(record):
    source = record.get('ligand') or record.get('file_ori_query') or ''
    return os.path.basename(source)


def related_files(stage, json_name):
    """Files copy_files() will look up for this pose, relative to the task dir."""
    stem = os.path.splitext(json_name)[0]
    found = []
    for folder in ('molecules', 'energies'):
        folder_path = os.path.join(stage, folder)
        if not os.path.isdir(folder_path):
            continue
        for name in sorted(os.listdir(folder_path)):
            if name == stem or name.startswith(stem + '.') or name.startswith(stem + '_'):
                found.append(folder + '/' + name)
    rel_json = 'energies/' + json_name
    if rel_json not in found:
        found.append(rel_json)
    return found


def build_index(energies_dir, out_path, ligands_list=None):
    stage = os.path.dirname(os.path.abspath(energies_dir))
    records = []
    found = set()
    for json_path in sorted(glob.glob(os.path.join(energies_dir, '*.json'))):
        with open(json_path) as handle:
            data = json.load(handle)
        json_name = os.path.basename(json_path)
        ligand = os.path.basename(data.get('file_ori_query') or json_name)
        found.add(ligand)
        try:
            num_execution = int(data.get('num_execution', -1))
        except (TypeError, ValueError):
            num_execution = -1
        records.append({
            'global_score': data.get('global_score', ''),
            'global_score_md': data.get('global_score_md', ''),
            'global_score_qu': data.get('global_score_qu', ''),
            'coords': data.get('coords', ['', '', '']),
            'num_execution': num_execution,
            'query': os.path.splitext(ligand)[0],
            'ligand': ligand,
            'json': 'energies/' + json_name,
            'files': related_files(stage, json_name),
        })

    if ligands_list:
        if not os.path.isfile(ligands_list):
            sys.stderr.write('ERROR: ligand list %s is gone; the task scratch was removed before indexing.\n' % ligands_list)
            return 1
        expected = []
        with open(ligands_list) as handle:
            for line in handle:
                line = line.strip()
                if line:
                    expected.append(os.path.basename(line))
        missing = [name for name in expected if name not in found]
    else:
        missing = []

    scored = []
    failed = list(missing)
    for record in records:
        if effective_score(record) is None:
            if record['ligand'] not in failed:
                failed.append(record['ligand'])
        else:
            scored.append(record)

    with open(out_path, 'w') as handle:
        for record in scored:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write('\n')
    failed_path = os.path.join(os.path.dirname(os.path.abspath(out_path)), 'failed.jsonl')
    with open(failed_path, 'w') as handle:
        for name in failed:
            handle.write(json.dumps({'ligand': name, 'reason': 'no_score'}, sort_keys=True))
            handle.write('\n')
    if failed:
        sys.stderr.write('WARNING: no score for %d ligand(s): %s\n' % (
            len(failed), ', '.join(failed[:20])))
    print('index: %d pose(s), %d without score -> %s' % (len(scored), len(failed), out_path))
    return 0


def iter_records(experiment):
    packed = os.path.join(experiment, 'packed')
    archives = sorted(glob.glob(os.path.join(packed, 'task_*.tar')))
    if not archives:
        raise SystemExit('ERROR: no packed/task_*.tar in %s' % experiment)
    for archive in archives:
        tar = tarfile.open(archive, 'r:')
        try:
            raw = tar.extractfile('index.jsonl')
            if raw is None:
                raise SystemExit('ERROR: %s has no index.jsonl' % archive)
            for line in raw:
                line = _text(line).strip()
                if not line:
                    continue
                record = json.loads(line)
                record['tar'] = archive
                yield record
        finally:
            tar.close()


def select_top(records, corte, n_keep):
    """Mirror ReadData: lock onto the first score sign, then keep the best n."""
    if n_keep <= 0:
        return []
    score_type = None
    heap = []
    seq = 0
    for record in records:
        score = effective_score(record)
        if score is None:
            continue
        if score == corte:
            print('Error score equals to threshold %s (%s)' % (corte, record.get('json')))
            continue
        kind = 'positivo' if score > corte else 'negativo'
        if score_type is None:
            score_type = kind
        if kind != score_type:
            continue
        seq += 1
        record = dict(record)
        record['_seq'] = seq
        record['_score'] = score
        if score_type == 'negativo':
            # Max-heap of the best (lowest) scores: the worst of them sits at the root.
            entry = (-score, seq, record)
            if len(heap) < n_keep:
                heapq.heappush(heap, entry)
            elif score < -heap[0][0]:
                heapq.heapreplace(heap, entry)
        else:
            entry = (score, seq, record)
            if len(heap) < n_keep:
                heapq.heappush(heap, entry)
            elif score > heap[0][0]:
                heapq.heapreplace(heap, entry)
    chosen = [entry[2] for entry in heap]
    if score_type == 'positivo':
        chosen.sort(key=lambda rec: (-rec['_score'], rec['_seq']))
    else:
        chosen.sort(key=lambda rec: (rec['_score'], rec['_seq']))
    return chosen


def _empty_tree(path):
    if os.path.isdir(path):
        for name in os.listdir(path):
            target = os.path.join(path, name)
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
    else:
        os.makedirs(path)


def _safe_member(name):
    parts = name.split('/')
    if name.startswith('/') or '..' in parts:
        raise SystemExit('ERROR: refusing to extract %s' % name)


def extract_records(chosen, experiment):
    by_archive = {}
    for record in chosen:
        by_archive.setdefault(record['tar'], []).append(record)
    for archive, records in by_archive.items():
        wanted = []
        for record in records:
            for name in record.get('files') or [record['json']]:
                _safe_member(name)
                if name not in wanted:
                    wanted.append(name)
        tar = tarfile.open(archive, 'r:')
        try:
            have = set(tar.getnames())
            for name in wanted:
                if name not in have:
                    raise SystemExit('ERROR: %s is not in %s' % (name, archive))
                tar.extract(name, path=experiment)
        finally:
            tar.close()


# A finished task may lack a score for a few ligands. The histogram still runs
# when those explicit failures stay within this percentage of ligands.list.
# Ligands in no task tar at all are unfinished work, not tolerated failures.
# MetaScreener -mf / --max-fail overrides the default (0 to 100).
FAILURE_PERCENT = 5


def failure_percent(value):
    try:
        percent = float(value)
    except (TypeError, ValueError):
        raise SystemExit('ERROR: --max-fail must be a percentage between 0 and 100')
    if percent != percent or percent < 0 or percent > 100:
        raise SystemExit('ERROR: --max-fail must be a percentage between 0 and 100')
    return percent


def iter_failures(experiment):
    packed = os.path.join(experiment, 'packed')
    for archive in sorted(glob.glob(os.path.join(packed, 'task_*.tar'))):
        tar = tarfile.open(archive, 'r:')
        try:
            try:
                raw = tar.extractfile('failed.jsonl')
            except KeyError:
                raw = None
            if raw is None:
                continue
            for line in raw:
                line = _text(line).strip()
                if not line:
                    continue
                record = json.loads(line)
                record['tar'] = archive
                yield record
        finally:
            tar.close()


def assess_coverage(experiment, max_fail=FAILURE_PERCENT):
    """Return (status, detail). status is ok, unknown or too_many."""
    max_fail = failure_percent(max_fail)
    manifest = os.path.join(experiment, 'ligands.list')
    if not os.path.isfile(manifest):
        return 'unknown', ['ligands.list']
    with open(manifest) as handle:
        expected = [os.path.basename(line.strip()) for line in handle if line.strip()]
    scored = set()
    for record in iter_records(experiment):
        if effective_score(record) is not None:
            scored.add(ligand_basename(record))
    failed = []
    seen = set()
    for record in iter_failures(experiment):
        name = os.path.basename(record.get('ligand') or '')
        if name and name not in scored and name not in seen:
            seen.add(name)
            failed.append(name)
    unknown = [name for name in expected if name not in scored and name not in seen]
    if unknown:
        return 'unknown', unknown
    if expected and len(failed) * 100 > len(expected) * max_fail:
        return 'too_many', failed
    return 'ok', failed


def materialize(experiment, rf, rb, corte, max_fail=FAILURE_PERCENT):
    experiment = os.path.abspath(os.path.normpath(experiment))
    max_fail = failure_percent(max_fail)
    status, detail = assess_coverage(experiment, max_fail)
    if status == 'unknown':
        sys.stderr.write('ERROR: %d ligand(s) have no finished task (not a recorded failure): %s\n' % (
            len(detail), ', '.join(detail[:20])))
        return 1
    if status == 'too_many':
        shown = int(max_fail) if max_fail == int(max_fail) else max_fail
        sys.stderr.write('ERROR: %d ligand(s) failed, above the %s%% limit: %s\n' % (
            len(detail), shown, ', '.join(detail[:20])))
        return 1
    if detail:
        print('tolerating %d ligand(s) without a score' % len(detail))

    records = list(iter_records(experiment))

    scores_path = os.path.join(experiment, 'packed', 'all_scores.txt')
    written = 0
    with open(scores_path, 'w') as handle:
        for record in records:
            score = effective_score(record)
            if score is None:
                continue
            handle.write('%s\n' % score)
            written += 1
    if written == 0:
        sys.stderr.write('ERROR: packed indexes have no scores\n')
        return 1

    n_keep = int(rf) + int(rb)
    chosen = select_top(records, float(corte), n_keep)
    if not chosen:
        sys.stderr.write('ERROR: no poses passed the score cutoff (%s)\n' % corte)
        return 1

    for folder in ('molecules', 'energies'):
        _empty_tree(os.path.join(experiment, folder))
    extract_records(chosen, experiment)
    print('materialize: %d score(s), extracted %d pose(s) into %s' % (
        written, len(chosen), experiment))
    return 0


def write_scoring_csv(experiment):
    experiment = os.path.abspath(os.path.normpath(experiment))
    rows = []
    for record in iter_records(experiment):
        score = effective_score(record)
        if score is None:
            continue
        coords = record.get('coords') or [0, 0, 0]
        while len(coords) < 3:
            coords.append(0)
        logical = os.path.splitext(os.path.abspath(os.path.join(experiment, record['json'])))[0]
        try:
            num_execution = int(record.get('num_execution', -1))
        except (TypeError, ValueError):
            num_execution = -1
        rows.append([
            score,
            float(coords[0]),
            float(coords[1]),
            float(coords[2]),
            record.get('query', ''),
            num_execution,
            logical,
        ])
    rows.sort(key=lambda row: row[0])
    out_path = os.path.join(experiment, 'Results_scoring.csv')
    with open(out_path, 'w') as handle:
        handle.write('Global score;x;y;z;Querie;Num_execution;Path\n')
        for row in rows:
            handle.write(';'.join(str(item) for item in row) + '\n')
    print('csv: %d row(s) -> %s' % (len(rows), out_path))
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description='Pack and read per-task VS tar archives.')
    sub = parser.add_subparsers(dest='cmd')

    index_cmd = sub.add_parser('index', help='write index.jsonl from a task energies/ directory')
    index_cmd.add_argument('--energies', required=True)
    index_cmd.add_argument('--out', required=True)
    index_cmd.add_argument('--ligands', default='')

    materialize_cmd = sub.add_parser('materialize', help='extract the top poses before the histogram')
    materialize_cmd.add_argument('--experiment', required=True)
    materialize_cmd.add_argument('--rf', type=int, required=True)
    materialize_cmd.add_argument('--rb', type=int, required=True)
    materialize_cmd.add_argument('--corte', type=float, default=0.0)
    materialize_cmd.add_argument('--max-fail', type=float, default=FAILURE_PERCENT,
                                 help='maximum percent of ligands.list allowed to lack a score')

    csv_cmd = sub.add_parser('csv', help='write Results_scoring.csv from every task index')
    csv_cmd.add_argument('--experiment', required=True)

    args = parser.parse_args(argv)
    if args.cmd == 'index':
        return build_index(args.energies, args.out, args.ligands or None)
    if args.cmd == 'materialize':
        return materialize(args.experiment, args.rf, args.rb, args.corte, args.max_fail)
    if args.cmd == 'csv':
        return write_scoring_csv(args.experiment)
    parser.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
