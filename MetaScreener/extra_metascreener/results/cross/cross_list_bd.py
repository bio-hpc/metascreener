# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Author: Jorge de la Peña García
#   Author: Carlos Martínez Cortés
#   Email:  cmartinez1@ucam.edu
#    
import sys
import json
import numpy
import math
import os
import re
import glob
from collections import OrderedDict

key_pat = re.compile(r"^(\D+)(\d+)$")
MAX_DISTANCE= 5
FAIL = '\033[91m'
WARNING = '\033[93m'
ENDC = '\033[0m'
FILE_CLUSTERS="{0}/{1}_clusters.json"
TOKEN_EMPTY = []
DEBUG = True

def print_error( lst_text ):    
    print ("")
    if isinstance(lst_text, list) :
        for text in lst_text:
            print(("{}Error:{} {} {}".format(FAIL,WARNING,text,ENDC)))
    else:
        print(("{}Error:{} {} {}".format(FAIL,WARNING,lst_text,ENDC)))
    print ("")
    exit()


def print_c(cl):
    if cl != TOKEN_EMPTY:
        for l in cl:
            print   '{}_{} {} {} {}'.format(l['sw'], l['cluster'], l['coords'], l['score'], l['lig_name'])
    else:
        print(TOKEN_EMPTY)
    print("")

def print_g(groups):
    for i in groups:
        print_c(i)

def print_s(text):
    print("__________________ {} _____________________________________________________________".format(text))

def key(item):
    m = key_pat.match(item[0])
    return m.group(1), int(m.group(2))


def key_2(item):
    return   (item[1][0]['score'])

def read_json(file ):
    with open(file) as json_file:
        data = json.load(json_file)
    data = sorted(data.items(),  key=key)
    return data
        
def distance_clusters(c_1, c_2):
    return math.sqrt((c_1[0] - c_2[0])**2 + (c_1[1] - c_2[1])**2+ (c_1[2] - c_2[2])**2)  

def find_name_rec_lig(folder, cl):
    pattern = folder + "/{}/{}_*{}"
    f_energies_json = glob.glob(pattern.format('energies', cl[0][1]['best_pose'], '.json'))[0]
    with open(f_energies_json) as json_file:  
        data = json.load(json_file)
    name_target = os.path.splitext(os.path.basename(data['file_ori_target']))[0]
    return name_target, data ['name']
    

def get_center_group(group):

    x = 0
    y = 0
    z = 0

    elemntes = len(group)
    
    for cluster in group:
        x += cluster['coords'][0]
        y += cluster['coords'][1]
        z += cluster['coords'][2]      
    return [ round (x/elemntes, 1), round(y/elemntes,1), round(z/elemntes,1) ]
    

    

"""
    Main
"""
format_text_10 = '{:>10}'
format_text = '{:>30}'
format_text_coord='{:>25}'
if ( len(sys.argv) < 2 ):
    print_error(['Introduce BD folders','BD_[A-Z][A-Z]_1le0_GLA*'])
array_bd_cl_folders = []
array_bd_cl = OrderedDict()


for i in range(1, len(sys.argv)):
    if not "tar.gz" in sys.argv[i] and os.path.exists(sys.argv[i]+"/energies" ):        
        array_bd_cl_folders.append(os.path.abspath(sys.argv[i]))

f_json_out = (os.path.basename( array_bd_cl_folders[0]).split("_")[2])+".json"
f_tex_out =os.path.splitext(f_json_out)[0] + '.tex'
f_excel_out =os.path.splitext(f_json_out)[0] + '.xls'
open(f_tex_out, 'w').close()
open(f_excel_out, 'w').close()

print_s('Read Data')
name_target = ""
for i in array_bd_cl_folders:
    sw = os.path.basename( i).split("_")[1]         
    data = read_json (FILE_CLUSTERS.format(i,os.path.basename(i) ) )
    if len(data) > 0:
        name_target, lig_name = find_name_rec_lig(i,data)  
        for j in data:
            j[1]['sw']=sw        
            j[1]['folder'] = i            
            j[1]['lig_name'] = lig_name

        aux_data = []
        for i in data:
            aux_data.append(i[1])    
        data = aux_data       
    
        if not lig_name in array_bd_cl:   
            array_bd_cl[lig_name] = data
        else:
            d = array_bd_cl[lig_name]    
            d += data
            array_bd_cl[lig_name] = d

array_bd_cl = OrderedDict( sorted(array_bd_cl.items(),  key=key_2)    )
for i, lst_cl in  array_bd_cl.items():
    array_bd_cl[i] = sorted(lst_cl, key=lambda k: k['score'])

total = 0
if DEBUG:
    for i, lst_cl in  array_bd_cl.items():
        print ("\n\n"+i)    

        for cl in lst_cl:
			total += 1  
			print (cl)
print_s('End Read Data')
print  ("\n\n")

print_s('Sort Data')
dict_clusters  = OrderedDict()
lst_off = []
for query, lst_cluter in array_bd_cl.items():

    del array_bd_cl [query]
    dict_clusters[query] = OrderedDict()
    cnt = 0
    for cl in lst_cluter:
        group = []
        if cl not in lst_off:
            lst_off.append(cl)
            group.append(cl)
            for cl_2 in lst_cluter:
                distance = distance_clusters( cl['coords'], cl_2['coords'])
                if  distance < MAX_DISTANCE:
                    if cl_2 not in lst_off:
                        print (cl['cluster'],cl['lig_name'],cl['sw'],  cl_2['cluster'], cl_2['lig_name'],cl_2['sw'])
                        group.append(cl_2)
                        lst_off.append(cl_2)


            dict_clusters[query][cnt] = group
            cnt += 1
print_s('End Sort Data')


"""
    Group cluster's centers and generate a hash and a json
"""

print_s('Group for print')
def get_format_cluster(cl, i ):
        return format_text.format('{}_{} {} {}'.format(cl['sw'], cl['cluster'], str(cl['score']), cl['lig_name']  ))
def get_format_cluster_latex(cl):
    return format_text.format('{}_{}_{}_{}'.format(cl['sw'], cl['cluster'], str(cl['score']), cl['lig_name']  ))
def print_rows(dict_groups):
    cnt_group = 0
    for key, row in dict_groups.items():

        max_len = 0
        for groups in row:
            if groups != TOKEN_EMPTY:
                if len(groups) > max_len:
                    max_len = len(groups)
        lst_txt = []
        lst_txt_latex = []
        for i in range(0, max_len):
            if i == 0:
                lst_txt.append(format_text_coord.format('{}_{}'.format(cnt_group,key)))
                lst_txt_latex.append(format_text_coord.format( '{}_{}'.format(cnt_group,key) ))
            else:
                lst_txt.append(format_text_coord.format(key))

                lst_txt_latex.append('*')

        cnt_cols = 0
        for groups in  row:
            if groups != TOKEN_EMPTY:
                aux =""
                cnt_cols += 1
                for i in range(0, max_len):
                    if len(groups) > i:
                        lst_txt[i] += get_format_cluster(groups[i], i)
                        lst_txt_latex[i] += get_format_cluster_latex(groups[i])
                    else:
                        lst_txt[i] += (format_text.format(TOKEN_EMPTY))
                        lst_txt_latex[i] += " & "

            else:
                cnt_cols += 1
                for i in range(0,max_len):
                    lst_txt[i] += format_text.format(TOKEN_EMPTY)
                    lst_txt_latex[i] += " -- "


        for i in range(0,len(lst_txt)):
            print(lst_txt[i] )


            i_latex = text_head = re.sub(' +', ' ', lst_txt_latex[i]).strip()
            i_latex= i_latex.replace(', ', ',')
            row_excel = ''
            row_latex = ''
            for j in i_latex.split(' '):
                row_excel += j +";"
                row_latex += '\\texttt{\detokenize{' + j + '}} & '
            row_latex = row_latex[:-2]
            row_excel = row_excel[:-1]
            row_excel = row_excel.replace("&","--")
            print_excel(row_excel)
            print_latex(row_latex +' \\\\')

        print_latex(amper_sand_latex+'\\\\')
        print_excel(amper_sand_latex.replace('&',';'))
        cnt_group += 1

        print ("")




clusterd_row_print = OrderedDict()
queries_header = "" 
text= format_text_coord.format("Coords")
lst_groups_off = []
def get_groups(group, offset_right):
    lst_groups = []
    for i in range(0, offset_right):
        lst_groups.append(TOKEN_EMPTY)
    cnt = 0
    lst_groups.append(group)

    lst_groups_off.append(group)
    cnt += 1
    center_group =  get_center_group(group)    
    for query, lst_group_clusters in dict_clusters.items():

        if query not in lst_queries_off:

            find= False
            for j in lst_group_clusters:
                distance = distance_clusters( center_group, get_center_group(lst_group_clusters[j]))

                if distance < MAX_DISTANCE:
                    if lst_group_clusters[j] not in lst_groups_off:
                        lst_groups.append(lst_group_clusters[j])
                        lst_groups_off.append(lst_group_clusters[j])
                        cnt += 1
                        find =  True
            if not find :
                lst_groups.append (TOKEN_EMPTY)
                cnt += 1

    offst_left = (len(dict_clusters) - offset_right) - cnt
    for i in range (0, offst_left):
      lst_groups.append (TOKEN_EMPTY)


    return center_group, lst_groups


def print_excel(text):
    f = open(f_excel_out, 'a')
    f.write(text + '\n')
    f.close()
def print_latex(text):
    f = open(f_tex_out, 'a')
    f.write(text+'\n')
    f.close()



def rectify_line(line):

    lst_queries = []
    print len(line)
    print len(dict_clusters)
    for i in line:
        print_c (i)



    for i in dict_clusters:
        lst_queries.append(i)

    lst_remove = 0
    while lst_remove != -1:
        lst_remove = -1
        cnt_queries = 0
        for i in range(0, len(line)):
            if len(line[i])  > 0:
                if len(lst_queries) <= cnt_queries or line[i][0]['lig_name'] != lst_queries[cnt_queries]:
                    lst_remove = i
                    for j in reversed(range(0,i)):
                        if line[i][0]['lig_name'] == line[i][0]['lig_name']:
                            for t in  range(0,len(line[i])):
                                line[i][t]['lig_name'] = line[i][t]['lig_name']+ '_(*)'

                            line[j] += line[i]
                            break;
                    del line[lst_remove]
                    break;
            cnt_queries += 1


offset_right = 0
lst_queries_off = []


for query, lst_group_clusters in dict_clusters.items():
    if query not in lst_queries_off:

        lst_queries_off.append(query)
        queries_header += format_text.format(query)
        if len (lst_group_clusters):
            for j in lst_group_clusters:
                if lst_group_clusters[j] not in lst_groups_off:
                    g, l = get_groups(lst_group_clusters[j], offset_right)

                    diff = len(l) - len(dict_clusters)
                    if diff != 0:
                        rectify_line(l)
                        clusterd_row_print[str(g)] = l
                    else:
                        clusterd_row_print[str(g)] = l
                    print (str(g))
                    print_g (l)
                    print ("\n")
        offset_right+=1


print_s('End Group for print')
print_s('Draw table centers groups')
header = format_text_coord.format("Coords")+queries_header
print (header)

for key, value in clusterd_row_print.items():
	aux = format_text_coord.format(key)
	for group in value:
		center_group =  get_center_group(group) if group != TOKEN_EMPTY else TOKEN_EMPTY
		aux += format_text.format(center_group)
	print(aux)
print ("")
print_s('End Draw table centers groups')

print_s('Paint table groups')
print ("\n\n")
print (header)
#
#   Latex
#
print_latex('\\documentclass{report}')
print_latex('\\usepackage{lscape}')
print_latex('\\begin{document}')
print_latex('\\begin{landscape}')
print_latex('\\begin{center}')
text_head = re.sub(' +', ' ', header).strip()
cols = ''
amper_sand_latex = ''
row_latex = ''
row_excel = ''
for i in text_head.split(' '):
    row_latex += '\\texttt{\detokenize{'+i+'}} & '
    row_excel += i+';'
    cols += 'l|'
    amper_sand_latex += '&'
cols = cols[:-1]
amper_sand_latex = amper_sand_latex[:-1]
row_latex = row_latex[:-2]

print_latex('\\begin{tabular}{'+cols+'}')
print_excel(row_excel)
print_latex (row_latex +'\\\\ \\hline \\hline')

print_rows(clusterd_row_print)

print_latex('\\end{tabular}')
print_latex('\\end{center}')
print_latex('\\end{landscape}')
print_latex('\\end{document}')

print_s('END Paint table groups')


s = json.dumps(clusterd_row_print, indent=4)
open(f_json_out, "w").write(s)



