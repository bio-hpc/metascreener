# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   Description: generates a csv with the euclidean distance between the ligand and each ligand in the database
   
"""
import argparse
import numpy as np
import operator
import subprocess

SEPARATOR = ','
MAX_COLUMNS = 10000
CUT_OFF = 0
DECIMALS_OUT = 5
DELIMITER_CSV = '\t'       
COL_START_DESCRIPTORS = 2   
#
# scopus search
#
SCOPUS_SCRIPT = 'MetaScreener/external_sw/scopus/scopus_search_matches.py'
PYTHON_RUN = 'python '
CMD_SCOPUS_SCRIPT = PYTHON_RUN+SCOPUS_SCRIPT+' {}'
CUT_OFF_SCOPUS = 100


def remove_empty_cols(matrix, head):
    lst_zero_descriptors = []
    lst_delete = [col for col in range(matrix.shape[1]) if matrix[:, col].max() == matrix[:, col].min()]
    for i in reversed(lst_delete):
        lst_zero_descriptors.append(head[i])
        matrix = np.delete(matrix, i, axis=1)
        head.pop(i)
    return lst_zero_descriptors, head, matrix


def create_matrix(lst_bbdd, lst_query, head):
    """
    :param lines:
    :param line_query:
    :return:
        Matrix normalised to 1
        ligand index
        ligand row to make distance
        ligand name
        modified head
        descriptors at 0
        
    """
    index_mol = []
    lst_bbdd.append(lst_query)
    aux_lst = []
    for i in lst_bbdd:
        index_mol.append('_'.join(i[:COL_START_DESCRIPTORS]))
        aux_lst.append(i[COL_START_DESCRIPTORS:])
    matrix = np.array(aux_lst).astype(np.float)
    """
        https://stackoverflow.com/questions/29661574/normalize-numpy-array-columns-in-python/44257532
    
        We normalise the range from minimum to maximum with minimum 0 and maximum 1.
        1º we subtract the minimum to all the columns
        2º divide by the range (i.e. the maximum)    
    """
    a = (matrix - matrix.min(0))
    lst_zero_descriptors, head, a = remove_empty_cols(a, head)
    b = a.ptp(0)
    x_n_matrix = a / b
    x_n_query = x_n_matrix[-1]
    x_n_matrix = x_n_matrix[:-1:]
    name_query = index_mol[len(index_mol)-1].split("_")[1]
    index_mol.pop()
    return x_n_matrix, index_mol, x_n_query, name_query, head, lst_zero_descriptors


def get_matches_scopus(mol_bbdd, mol_query):
    search = '"{}+{}"'.format(mol_bbdd, mol_query)
    return subprocess.check_output(CMD_SCOPUS_SCRIPT.format(search),  shell=True).decode('UTF-8')


def dist_euclidian(x, y):
    """
        Calculates euclidian distance
    :param x:
    :param y:
    :return:
    """
    return np.sqrt(np.sum((x-y)**2))


def get_similar_descriptors(x_n_row, x_n_query, head):
    lst_aux = []
    for i in range(len(x_n_row)):
        diff = abs(x_n_row[i] - x_n_query[i])
        if diff <= CUT_OFF:
            lst_aux.append(head[i])
    return lst_aux


def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_database', type=argparse.FileType('r'))
    parser.add_argument('file_query', type=argparse.FileType('r'))
    parser.add_argument('out_put', type=argparse.FileType('w'))
    parser.add_argument('-s', '--show_descriptors', help='Show descriptors', default=True)
    parser.add_argument('-d', '--debug', action='store_true', help='print debug messages to stderr')
    return parser.parse_args()


def euclidiana(x_n_matrix, index_mol, x_n_query, head, name_lig):
    """

    :param x_n_matrix:
    :param index_mol:
    :param x_n_query:
    :return:
        ordered list with the molecule and its distance
    """
    dct = {}
    for i in range(len(index_mol)):
        dist = dist_euclidian(x_n_matrix[i], x_n_query)
        lst_descriptors = get_similar_descriptors(x_n_matrix[i], x_n_query, head)
        key = index_mol[i].split('_')
        key = '{}, {}'.format( key[1], key[0].replace(',', '_'))
        dct[key] = [name_lig, round(dist, DECIMALS_OUT), ', '.join(lst_descriptors)]
    return sorted(dct.items(), key=operator.itemgetter(1))


lst_query_cols = []  # number of columns to be saved
head = []   # Header for descriptors
aux_head = []   
lst_bbdd = [] 
cnt_all_molecules = 0   
args = get_parameters()

#
#  Read non NaN columns of query
#
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

cnt = 1
f = open(args.out_put.name, 'w')
f.write("\nTotal Molecules: {}\n".format(cnt_all_molecules))
f.write("All descriptors: {}\n".format(all_descriptores))
f.write("Descriptors No Nan: {}\n".format(descriptors_no_nan))
f.write('Molecules: {} + 1 query\n'.format(len(x_n_matrix)))
f.write('\n{}, {}, {}, {}, {}, {}, {}, {}\n'.format('Rank', 'BBDD_Mol', 'Name', 'Scopus_matches', 'Nº descriptors', 'Query', 'D euclidian',  'Descriptors'))
for row in sorted_x:
    str_aux = ""
    for col in range(len(row[1])):
        if col < COL_START_DESCRIPTORS:
            str_aux += '{}{}'.format(row[1][col], SEPARATOR)
        elif args.show_descriptors == True:
            str_aux += '{}{}'.format(row[1][col], SEPARATOR)
    scopus_search = ''
    if cnt < CUT_OFF_SCOPUS:
        mol_query = str_aux.split(',')[0]
        mol_bbdd = row[0].split(',')[1].strip()
        scopus_search = get_matches_scopus(mol_bbdd, mol_query).strip()

    else:
        scopus_search = '-'
    str_aux = str_aux.replace(',,', ',')
    str_aux = str_aux.strip()[:str_aux.rindex(',')]
    str_aux = '{}, {}, {}'.format(scopus_search, len(str_aux.split(SEPARATOR))-COL_START_DESCRIPTORS, str_aux)
    f.write('{}, {}, {}\n'.format(cnt, row[0], str_aux))
    cnt += 1






f.write('___________________________________________________________________________________________________________\n')
f.write('All columns with the same descriptors = {} \n{}\n'.format(len(lst_zero_descriptors),', '.join(lst_zero_descriptors)))
f.write('___________________________________________________________________________________________________________\n')

f.close()

