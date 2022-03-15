#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Author: Jorge de la Peña garcía
    Author: Carlos Martínez Cortés
    Email: cmartinez1@ucam.edu
    Description: Join experiments conducted with LS by metascreener in a single file to visualize them with ligandscout and excel. Also works with multiple runs of the same target protein with different ligands.

"""
import argparse
from functools import partial
from glob import glob
from os.path import isdir, join
from os import stat
import os
import subprocess


FOLDER_MOLECULES = 'molecules'
TAG_END_MOL = '$$$$'
TAG_SCORE = '> <Score>'
TAGS_NAME = [ 'DATABASE_ID',  'VillaPharma_Code', 'idnumber'] #special case for the name of the molecules VP and drugbank
SEARCH_MATCHES = "MetaScreener/extra_metascreener/scopus/scopus_search_matches.py"
PYTHON_RUN = "python"
F_SEARCH_MATCHES = PYTHON_RUN+" "+SEARCH_MATCHES+" \'{}\'"

def read_names(filename):
	dct_name = {}
	f = open(filename)
	for i in f:
		code = i.split("|")[1].strip().replace("'",("")).replace(";","_")
		name = i.split("|")[0].strip().replace("'",("")).replace(";","_")

		dct_name [code] = name

	return dct_name

def write_excel(lst_molecules, prefix):
	f = open(prefix+".csv", 'w')
	for i in lst_molecules:  
		f.write('{}\n'.format(i))
	f.close()
	if not args.summary:
	    try:
		    import pandas as pd
		    read_file = pd.read_csv (prefix+".csv", delimiter=';')
		    read_file.to_excel (prefix+'.xlsx', index = None, header=True, engine='xlsxwriter')
				
	    except Exception as e:
		    print ("Error convert csv to xlsx")
		    print (e)

def write_file(lst_molecules, prefix_name):
	"""
		Write all molecules in the output file
		:param lst_molecules:
		:return:
	"""
	out = prefix_out+".sdf"
	
	f = open(out, "w")
	for line in lst_molecules:
		f.write('{}\n'.format(line))
	f.close()   

	


def check_molecule(molecule):
    """
        Check that the molecule has the appropriate score, higher than the cut, if the true result is higher if it is lower false.
        :param molecule:
        :return:
    """

    for cnt_line in range(len(molecule)):
        if TAG_SCORE in molecule[cnt_line]:            
            if args.c <= float(molecule[cnt_line+1]):
                return True
    return False


def clean_firs_line_molecule(molecule):
    """
        The sdf files cannot start a blank line, this function removes that line if it exists.
        :return:
    """    
    if molecule[0] == '':
        molecule.pop(0)    
    return molecule


def get_name_molecule(molecule):
    """
        return the name of the molecule
        :param str molecule:
    """
    for cnt_line in range(0, len(molecule)):        
        for tag_name in TAGS_NAME:
            if tag_name in molecule[cnt_line]:
                return (molecule[cnt_line+1])
                
    if molecule[0] != '':
        return molecule[0]
    else:
        print ("Error No name for molecule")
        exit(0)


def get_score_molecule(molecule):
    """
        Return score fo molecule
        :param molecule:
    """
    for cnt_line in range(len(molecule)):
        if TAG_SCORE in molecule[cnt_line]:
            return float(molecule[cnt_line+1])
    return 0


def read_molecules(dict_molecules, f_sdf, m_duplicate, m_swap, m_total, m_cutoff, dic_molecules_insert):
    """
        Reads an sdf file, separates the moleulas by the delimiter and if score is better than cut-off stores it in a list
        :param f_sdf:
        :return:
    """
    f = open(f_sdf)
    molecule = []
    for line in f:
        molecule.append(line[:-1])
        if TAG_END_MOL in line:
            m_total += 1
            if check_molecule(molecule):
                m_cutoff += 1
                molecule = clean_firs_line_molecule(molecule)
                name_molecule = get_name_molecule(molecule)
                score = get_score_molecule(molecule)
                if name_molecule in dict_molecules:
                    m_duplicate += 1
                    score_saved_molecule = get_score_molecule(dict_molecules[name_molecule])
                    if args.debug:
                        print ('Molecule duplicate: {:>10} \tscore molecule {:>10}\t score saved molecule {:>10}'.format(name_molecule,
                                                                score, score_saved_molecule))
                    if score > score_saved_molecule:
                        m_swap += 1
                        if args.debug:
                            print (
                                'Molecule Swap: {:>10} \tscore molecule {:>10}\t score saved molecule {:>10}'.format(
                                    name_molecule,
                                    score, score_saved_molecule))
                        dict_molecules[name_molecule] = molecule
                        dic_molecules_insert [name_molecule] = score;
                else:                                      
                    if not name_molecule.strip().startswith("0"):
                    	if args.debug:
                        	print ('Molecule Inert: {:>10} \tscore {:>10}'.format(name_molecule, score))                    	
                    	dic_molecules_insert [name_molecule] = score;
                    	dict_molecules[name_molecule] = molecule
            molecule = []
    f.close()
    return dict_molecules, m_duplicate, m_swap, m_total, m_cutoff, dic_molecules_insert


parser = argparse.ArgumentParser(
    description='Join experiments conducted with LS by metascreener in a single file to visualize them with ligandscout and excel. Also works with multiple runs of the same target protein with different ligands.',
    epilog="""Example of use: 
           python MetaScreener/extra_metascreener/results/join/join_ls_sessions.py LS_6ioz_LBVS_with_excl_v1_DBALLv503_a_""",
    formatter_class=partial(argparse.ArgumentDefaultsHelpFormatter, width=500)
)
parser.add_argument('prefix', type=str, help='Prefix of input dirs')
parser.add_argument('-c', type=float, help='cut-off', default=0.7)
parser.add_argument('-q', '--query', type=str, help=argparse.SUPPRESS)
parser.add_argument('-f', '--file_name', type=argparse.FileType('r'), help='file with names of molecules (CODE|NAME)')
parser.add_argument('-s', '--summary',  help='Returns only a csv summary with all hits from a Metascreener run with Ligand scout.', action='store_true')
parser.add_argument('-d', '--debug',  help='debug', action='store_true')
args = parser.parse_args()
dct_names = {}
if args.file_name:
	dct_names = read_names(args.file_name.name)

if args.summary:
    args.c=0

m_duplicate = 0
m_total = 0
m_cutoff = 0
m_swap = 0
dic_molecules_insert = {}
if args.prefix[len(args.prefix)-1] == '/':
    args.prefix=args.prefix[:-1]

lst_dirs = sorted(glob('{}*'.format(args.prefix)))
dict_molecules = {}  # Stores valid molecules
if len(lst_dirs) == 0:
    print ("Error not directories with this prefix were found")
    exit(0)
dir_aux = ""
dict_experiments = {}
for directory in lst_dirs:

	if os.path.isdir(directory):	
		if dir_aux != directory[:directory.rindex("_")]:
			print (dir_aux, directory)
		
			if dir_aux != "":
				dict_experiments[dir_aux] = {
					'dict_molecules': dict_molecules,
					'm_swap': m_swap,
					'm_total': m_total,
					'm_cutoff':m_cutoff,
					'm_duplicate': m_duplicate,
					'dic_molecules_insert':dic_molecules_insert
				}
				
				m_duplicate = 0
				m_total = 0
				m_cutoff = 0
				m_swap = 0	
				m_duplicate = 0
				dic_molecules_insert = {}
				dict_molecules = {}
			dir_aux=directory[:directory.rindex("_")]			

		if isdir(directory):				
			sdfs = join(directory, FOLDER_MOLECULES, '*.sdf')
			lst_sdfs = glob(sdfs)
			for f_sdf in lst_sdfs:
				if stat(f_sdf).st_size == 0:
				    print ('File is empty: {}'.format(f_sdf))
				else:
				    dict_molecules, m_duplicate, m_swap, m_total, m_cutoff, dic_molecules_insert = read_molecules(dict_molecules, f_sdf,  m_duplicate, m_swap, m_total ,m_cutoff,dic_molecules_insert)

dict_experiments[dir_aux] = {
			'dict_molecules': dict_molecules,
			'm_swap': m_swap,
			'm_total': m_total,
			'm_cutoff':m_cutoff,
			'm_duplicate': m_duplicate,
			'dic_molecules_insert':dic_molecules_insert
}		

print ("\n\n")	
dict_experiments_all = {}
for i in dict_experiments:
	lst_molecules = []
	for k, v in dict_experiments[i]['dict_molecules'].items():
	    for j in v:
	        lst_molecules.append (j)
	if args.debug:
		print('{} '.format(i))
		print ("\n\nCut-off: {:>20}".format(args.c))
		print ("Molecules Total: {:>12}".format(dict_experiments[i]['m_total']))
		print ("Molecules cutoff: {:>11}".format(dict_experiments[i]['m_cutoff']))

		print ("Molecules duplicate: {:>8}".format(dict_experiments[i]['m_duplicate']))
		print ("Molecules swap: {:>13}".format(dict_experiments[i]['m_swap']))
		print ("Molecules Saved: {:>12}\n".format(len(dict_experiments[i]['dict_molecules'])))

	dict_experiments[i]['dic_molecules_insert'] = sorted(dict_experiments[i]['dic_molecules_insert'] .items(), key=lambda x: x[1], reverse=True)
	print ("\nRank:\n")
	cnt = 0
	for mol in dict_experiments[i]['dic_molecules_insert']:
		dict_experiments_all[i+"|"+mol[0]] = mol[1]	
		cnt += 1
		print ('{:>10}º{:>20}{:>20}'.format(cnt, mol[0],round(mol[1],4)))
	print ("\n")
	prefix_out = '{}all'.format(i) if args.prefix.endswith('\_') else '{}_all'.format(i)
	if not args.summary:
	    write_file(lst_molecules, prefix_out)

print ("\nRank All:\n")
cnt = 0
dict_experiments_all= sorted(dict_experiments_all .items(), key=lambda x: x[1], reverse=True)

lst_excel = []
lst_excel.append('{};{};{};{};{};{}'.format('Rank', 'Experiment', 'Code', 'Score', 'Matches', 'Query'))
print ('{:>5}º{:>40}{:>20}{:>20}{:>10}{:>60}'.format('Rank', 'Experiment', 'Code', 'Score', 'Matches', 'Query'))
for i in dict_experiments_all:
	cnt+= 1
	name = i[0].split("|")[0].split("/")[-1]
	code = i[0].split("|")[1]
	matches = "--"
	query = "--"

	if code in dct_names:
		if str(args.query).strip() == "":
			query = dct_names[code].strip()

			cmd = F_SEARCH_MATCHES.format(query)
		else:
			query = (dct_names[code]+" AND "+str(args.query)).strip()
			cmd = F_SEARCH_MATCHES.format(query)
		if os.path.isfile(SEARCH_MATCHES):
		    output = subprocess.check_output(
        	    cmd,
        	    shell=True,
        	    stderr=subprocess.STDOUT,
    	    )
		matches = output.decode('utf-8') 
	lst_excel.append('{};{};{};{};{};{}'.format(cnt ,name, code, i[1], matches.strip(), query.strip()))
	print ('{:>5}º{:>40}{:>20}{:>20}{:>10}{:>60}'.format(cnt ,name, code, i[1], matches.strip(), query.strip()))
write_excel(lst_excel, args.prefix)
