# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   Author: Jorge de la Peña García
   Email:  jpena@ucam.edu
   Description: Generates a csv with the euclidian distance between the ligand and each ligand in the database
"""
import argparse
import numpy as np
import operator
import subprocess
from os.path import splitext

SEPARATOR = '|'
SEPARATOR_NAME_MOL = '__-__'
MAX_COLUMNS = 10000
CUT_OFF = 0
DECIMALS_OUT = 5
DELIMITER_CSV = '\t'
COL_START_DESCRIPTORS = 2
CUT_OFF_RESUME = 100

SCOPUS_SCRIPT = 'MetaScreener/extra_metascreener/scopus/scopus_search_matches.py'
PYTHON_RUN = 'python '
CMD_SCOPUS_SCRIPT = PYTHON_RUN+SCOPUS_SCRIPT+' {}'
CUT_OFF_SCOPUS = 100


def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def remove_empty_cols(matrix, head):
    lst_zero_descriptors = []
    lst_delete = [col for col in range(matrix.shape[1]) if matrix[:, col].max() == matrix[:, col].min()]
    for i in reversed(lst_delete):
        lst_zero_descriptors.append(head[i])
        matrix = np.delete(matrix, i, axis=1)
        head.pop(i)
    return lst_zero_descriptors, head, matrix


def create_matrix(lst_bbdd, lst_query, head):
    index_mol = []
    lst_bbdd.append(lst_query)
    aux_lst = []
    for i in lst_bbdd:
        index_mol.append(SEPARATOR_NAME_MOL.join(i[:COL_START_DESCRIPTORS]))
        aux_lst.append(i[COL_START_DESCRIPTORS:])
    matrix = np.array(aux_lst).astype(np.float)
    a = (matrix - matrix.min(0))
    lst_zero_descriptors, head, a = remove_empty_cols(a, head)
    b = a.ptp(0)
    x_n_matrix = a / b
    x_n_query = x_n_matrix[-1]
    x_n_matrix = x_n_matrix[:-1:]

    name_query = index_mol[len(index_mol)-1].split(SEPARATOR_NAME_MOL)[1]
    index_mol.pop()
    return x_n_matrix, index_mol, x_n_query, name_query, head, lst_zero_descriptors


def get_matches_scopus(mol_bbdd, mol_query):
    print (mol_bbdd);
    mol_bbdd = mol_bbdd.replace("\"","").replace("'","");
    print (mol_bbdd);
    search = '"{}+{}"'.format(mol_bbdd, mol_query)
    return subprocess.check_output(CMD_SCOPUS_SCRIPT.format(search),  shell=True).decode('UTF-8')


def dist_euclidian(x, y):
    return np.sqrt(np.sum((x-y)**2))


def get_similar_descriptors(x_n_row, x_n_query, head):
    lst_aux = []
    for i in range(len(x_n_row)):
        diff = abs(x_n_row[i] - x_n_query[i])
        if diff <= CUT_OFF:
            lst_aux.append(head[i])
    return lst_aux


def file_write(f_1, f_2, cnt, txt):
    f_1.write(txt)
    if cnt < CUT_OFF_RESUME + 1:
        f_2.write(txt)


def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_database', type=argparse.FileType('r'))
    parser.add_argument('file_query', type=argparse.FileType('r'))
    parser.add_argument('out_put', type=argparse.FileType('w'))
    parser.add_argument('-s', '--show_descriptors', type=str2bool, help='Show descriptos', default=True)
    parser.add_argument('-b', '--bibliographic', type=str2bool, help='bibliographic search of the 100 best', default=True)
    parser.add_argument('-d', '--debug', action='store_true', help='print debug messages to stderr')
    return parser.parse_args()


def euclidiana(x_n_matrix, index_mol, x_n_query, head, name_lig):
    dct = {}
    for i in range(len(index_mol)):
        dist = dist_euclidian(x_n_matrix[i], x_n_query)
        lst_descriptors = get_similar_descriptors(x_n_matrix[i], x_n_query, head)
        key = index_mol[i].split(SEPARATOR_NAME_MOL)
        key = '{}{} {}'.format( key[1], SEPARATOR, key[0].replace(',', '_'))
        dct[key] = [name_lig, round(dist, DECIMALS_OUT), '{} '.format(SEPARATOR).join(lst_descriptors)]

    return sorted(dct.items(), key=operator.itemgetter(1))


lst_query_cols = []
head = []
aux_head = []
lst_bbdd = []
cnt_all_molecules = 0
args = get_parameters()
format_head = ' {}'.format(SEPARATOR).join(['Rank', 'BBDD_Mol', 'Name', 'Scopus_matches', 'Nº descriptors', 'Query', 'D euclidian',  'Descriptors'])


f_in = open(args.file_query.name)
lst_quey = []
aux_head = f_in.readline().split(DELIMITER_CSV)
line = f_in.readline().strip()
all_descriptores = 0
if line != "":
    cols = line.split(DELIMITER_CSV)
    all_descriptores = len(cols)
    cnt_addition_cols = 0
    for cnt_col in range(len(cols)):
        if cnt_addition_cols > MAX_COLUMNS:
            break;
        if cols[cnt_col] != "NaN":
            lst_quey.append(cols[cnt_col])
            lst_query_cols.append(cnt_col)
            head.append(aux_head[cnt_col].strip())
            cnt_addition_cols += 1
f_in.close()
head = head[COL_START_DESCRIPTORS:]

f_in = open(args.file_database.name)
f_in.readline().split(DELIMITER_CSV)
for line in f_in:
    filter_line = []
    right = False
    aux = line.strip()
    if aux != "":
        aux = aux.split(DELIMITER_CSV)
        for n_col in lst_query_cols:
            if aux[n_col] == "NaN":
                right = False
                break
            else:
                right = True;
                filter_line.append(aux[n_col])
    if right:
        lst_bbdd.append(filter_line)
    cnt_all_molecules += 1
f_in.close()
if len(lst_bbdd) == 0:
    print ("No molecules have been found with the characteristics of the ligand")
    exit()
if args.debug:
    for i in lst_bbdd:
        print (i)
    print (head)
    print (lst_query_cols)
descriptors_no_nan = len(head)

x_n_matrix, index_mol, x_n_query, namne_lig, head, lst_zero_descriptors = create_matrix(lst_bbdd, lst_quey, head)
sorted_x = euclidiana(x_n_matrix, index_mol, x_n_query, head, namne_lig)

f_resume = open(splitext(args.out_put.name)[0]+'_100.csv', 'w')
f = open(args.out_put.name, 'w')

file_write(f, f_resume, 0, "\nTotal Molecules: {}\n".format(cnt_all_molecules))
file_write(f, f_resume, 0, "All descriptors: {}\n".format(all_descriptores))
file_write(f, f_resume, 0, "Descriptors No Nan: {}\n".format(descriptors_no_nan))
file_write(f, f_resume, 0, 'Molecules: {} + 1 query\n'.format(len(x_n_matrix)))
format_head = '{} '.format(SEPARATOR).join(['Rank', 'BBDD_Mol', 'Name', 'Scopus_matches', 'Nº descriptors', 'Query', 'D euclidian',  'Descriptors'])
file_write(f, f_resume, 0, '{}\n'.format(format_head))
cnt = 1
for row in sorted_x:
    str_aux = ""
    for col in range(len(row[1])):
        if col < COL_START_DESCRIPTORS:
            str_aux += '{}{}'.format(row[1][col], SEPARATOR)
        elif args.show_descriptors:
            str_aux += '{}{}'.format(row[1][col], SEPARATOR)
    scopus_search = ''
    if cnt < CUT_OFF_SCOPUS and args.bibliographic:
        mol_query = str_aux.split(SEPARATOR)[0]
        mol_bbdd = row[0].split(SEPARATOR)[1].strip()
        scopus_search = get_matches_scopus(mol_bbdd, mol_query).strip()

    else:
        scopus_search = '-'
    str_aux = str_aux.replace('{}{}'.format(SEPARATOR, SEPARATOR), SEPARATOR)
    str_aux = str_aux.strip()[:str_aux.rindex(SEPARATOR)]
    n_descs = str(len(str_aux.split(SEPARATOR)) - COL_START_DESCRIPTORS)
    str_aux = '{} '.format(SEPARATOR).join([scopus_search, n_descs, str_aux])
    #str_aux = '{}, {}, {}'.format(scopus_search, len(str_aux.split(SEPARATOR))-COL_START_DESCRIPTORS, str_aux)
    str_aux = '{} '.format(SEPARATOR).join([str(cnt), row[0], str_aux])
    file_write(f, f_resume, cnt, '{}\n'.format(str_aux))
    cnt += 1

file_write(f, f_resume, 0, '___________________________________________________________________________________________________________\n')
file_write(f, f_resume, 0, 'All columns with the same descriptors = {} \n{}\n'.format(len(lst_zero_descriptors), '{} '.format(SEPARATOR).join(lst_zero_descriptors)))
file_write(f, f_resume, 0, '___________________________________________________________________________________________________________\n')

f.close()
f_resume.close()
try:
    import pandas as pd

    p_resume = '{}_100.xlsx'.format( splitext(args.out_put.name)[0] )
    p_out_put = '{}.xlsx'.format(splitext(args.out_put.name)[0])

    read_file = pd.read_csv(splitext(args.out_put.name)[0]+'_100.csv')
    read_file.to_excel(p_resume, index=None, header=True, engine='xlsxwriter')

    read_file = pd.read_csv(args.out_put.name)
    read_file.to_excel(p_out_put, index=None, header=True, engine='xlsxwriter')
except:
  print("Error: No pandas module found")

