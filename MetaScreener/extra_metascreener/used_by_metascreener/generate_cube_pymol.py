#!/usr/bin/env python2

import sys
import itertools
import numpy as np

if len(sys.argv)!=3:
	print("error")
	print("Itroduce a center point and a grid size")
	print("ejemplo: python generateCubePymol.py 45::65::78 25")
	exit()
#
#	Cube center
#
CentroX=float(sys.argv[1].split("::")[0])
CentroY=float(sys.argv[1].split("::")[1])
centroZ=float(sys.argv[1].split("::")[2])
centro=np.array([CentroX,CentroY,centroZ])

tam=float(sys.argv[2])/2
lista=[]

for i in itertools.product([ -1, 1], repeat=3):
	res=centro+tam *np.array(i)
	lista.append("VERTEX, "+str(round(res[0],3))+" , "+str(round(res[1],3))+" , "+str(round(res[2],3))+" , ")

lista.append(lista[0]+lista[2])
lista.append(lista[2]+lista[6])
lista.append(lista[4]+lista[6])
lista.append(lista[0]+lista[4])

lista.append(lista[1]+lista[3])
lista.append(lista[1]+lista[5])
lista.append(lista[5]+lista[7])
lista.append(lista[3]+lista[7])
var="[ BEGIN, LINES, COLOR, 0.09, 0.61, 0.85, "
for i in lista:
	var+=i
var+="  END ]"
print (var)



