#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Carlos Martínez Cortés
# Email:  cmartinez1@ucam.edu
# Description: Translate the atom IDs given to -metal (IDs of the target mol2) into the
#              atom indexes used internally by Leadfinder.
#              Leadfinder reorders the receptor atoms by residue and expects in -metal A,B
#              the 0-based position of the atom in its own model, not the mol2 ID.
#              The script prints the translated -metal options to stdout.
#_________________________________________________________________________________________________________________________________________________________________________
import argparse
import os
import subprocess
import sys

TOKEN_ATOM = '@<TRIPOS>ATOM'
COORD_TOLERANCE = 0.01  # Angstrom
METALS = {
    'LI', 'NA', 'K', 'RB', 'CS', 'BE', 'MG', 'CA', 'SR', 'BA', 'AL', 'GA', 'IN', 'TL', 'SN', 'PB', 'BI',
    'SC', 'TI', 'V', 'CR', 'MN', 'FE', 'CO', 'NI', 'CU', 'ZN', 'Y', 'ZR', 'NB', 'MO', 'TC', 'RU', 'RH',
    'PD', 'AG', 'CD', 'HF', 'TA', 'W', 'RE', 'OS', 'IR', 'PT', 'AU', 'HG', 'LA', 'CE', 'PR', 'ND', 'SM',
    'EU', 'GD', 'TB', 'DY', 'HO', 'ER', 'TM', 'YB', 'LU', 'U',
}


def fail(msg):
    sys.stderr.write('{}\n'.format(msg))
    sys.exit(1)


def read_mol2_atoms(file_name):
    atoms = []
    in_atoms = False
    with open(file_name) as f:
        for line in f:
            if line.startswith('@<TRIPOS>'):
                in_atoms = line.strip() == TOKEN_ATOM
                continue
            fields = line.split()
            if in_atoms and len(fields) >= 6:
                atoms.append({
                    'id': int(fields[0]),
                    'name': fields[1],
                    'coords': (float(fields[2]), float(fields[3]), float(fields[4])),
                    'element': fields[5].split('.')[0].upper(),
                    'residue': fields[7] if len(fields) > 7 else '',
                })
    return atoms


def parse_metal_options(lf_metal):
    """Split ' -metal 3000,6 -metal reference none' into [['3000,6'], ['reference', 'none']]"""
    options = []
    for token in lf_metal.split():
        if token == '-metal':
            options.append([])
        elif options:
            options[-1].append(token)
    return options


def run_leadfinder(leadfinder, target, workdir):
    debug_dir = os.path.join(workdir, 'debug')
    cmd = [leadfinder, '--check-only={}'.format(os.path.join(workdir, 'check.log')),
           '--protein={}'.format(target), '--debug={}'.format(debug_dir)]
    with open(os.path.join(workdir, 'leadfinder.out'), 'w') as out:
        subprocess.call(cmd, stdout=out, stderr=subprocess.STDOUT)
    model = os.path.join(debug_dir, 'protein.mol2')
    if not os.path.isfile(model):
        with open(os.path.join(workdir, 'leadfinder.out')) as out:
            lines = [line.strip() for line in out if line.strip()]
        fail('-metal: Leadfinder could not build the receptor model ({})'.format(' '.join(lines[-3:])))
    return model


def find_lf_index(atom, lf_atoms):
    matches = [i for i, lf_atom in enumerate(lf_atoms)
               if all(abs(a - b) <= COORD_TOLERANCE for a, b in zip(atom['coords'], lf_atom['coords']))]
    if len(matches) != 1:
        fail('-metal: atom {} ({} {}) found {} times in the Leadfinder receptor model'.format(
            atom['id'], atom['name'], atom['residue'], len(matches)))
    return matches[0]


def parse_option(option, target_atoms):
    """Return (prefix, atom, coordination) of a -metal option. atom is None for '-metal reference X'"""
    if option[:1] == ['reference']:
        prefix, values = option[:2], option[2:]
    else:
        prefix, values = [], option
    if not values:
        return prefix, None, None

    values = ','.join(values).split(',')
    if len(values) != 2 or not all(v.isdigit() for v in values):
        fail('-metal: wrong value "{}", expected ATOM_ID,COORDINATION'.format(' '.join(option)))
    atom_id, coordination = int(values[0]), values[1]

    atom = target_atoms.get(atom_id)
    if atom is None:
        fail('-metal: atom ID {} does not exist in the target'.format(atom_id))
    if atom['element'] not in METALS:
        fail('-metal: atom {} ({} {}) is not a metal (element {})'.format(
            atom_id, atom['name'], atom['residue'], atom['element']))
    return prefix, atom, coordination


def main():
    parser = argparse.ArgumentParser(description='Translate mol2 atom IDs of -metal options into Leadfinder indexes')
    parser.add_argument('--leadfinder', required=True, help='Leadfinder executable')
    parser.add_argument('--target', required=True, help='Target mol2 file')
    parser.add_argument('--workdir', required=True, help='Directory for Leadfinder temporary files')
    parser.add_argument('--metal', required=True, help='-metal options as given to MetaScreener')
    args = parser.parse_args()

    target_atoms = {atom['id']: atom for atom in read_mol2_atoms(args.target)}
    options = [parse_option(option, target_atoms) for option in parse_metal_options(args.metal)]
    lf_atoms = []
    if any(atom is not None for _, atom, _ in options):
        lf_atoms = read_mol2_atoms(run_leadfinder(args.leadfinder, args.target, args.workdir))

    translated = []
    for prefix, atom, coordination in options:
        values = prefix
        if atom is not None:
            lf_index = find_lf_index(atom, lf_atoms)
            sys.stderr.write('-metal: atom {} ({} {}) -> Leadfinder index {}\n'.format(
                atom['id'], atom['name'], atom['residue'], lf_index))
            values = prefix + ['{},{}'.format(lf_index, coordination)]
        translated.append('-metal {}'.format(' '.join(values)))
    print(' '.join(translated))


if __name__ == '__main__':
    main()
