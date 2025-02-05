#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Carlos Martínez Cortés
# Email:  cmartinez1@ucam.edu
# Description: Get the center of a ligand
#_________________________________________________________________________________________________________________________________________________________________________
import os,sys,re

ll=()
valoresCoordenadas=[0,0,0]
nAtom=0;

def get_com():
	global nAtom;
	if extension == ".mol2":
		if contadorDeModelo== 1 and linea.find("@<TRIPOS>ATOM")==-1:
			nAtom+=1;
			ll=linea.split( );
			valoresCoordenadas[0]+=float (ll[2]);
			valoresCoordenadas[1]+=float(ll[3]);
			valoresCoordenadas[2]+=float(ll[4]);
	else:
		if contadorDeModelo==1 and ('ATOM ' in linea or 'HETATM ' in linea ) :
			nAtom+=1;
			x=linea.split()[6]
			y=linea.split()[7]
			z=linea.split()[8]
			valoresCoordenadas[0]+=float(x);
			valoresCoordenadas[1]+=float(y);
			valoresCoordenadas[2]+=float(z);
#
#	Main
#
if len(sys.argv) != 2:
	print ("script get_center_ligand.py")
	print ("Introduce a query for calculate it center")
	exit();
ligand = sys.argv[1]
filename, extension = os.path.splitext(ligand)

f=open(ligand);
contadorDeModelo=0;
for linea in f:
	if  "ENDMDL" in linea or "MODEL" in linea or len(re.findall('\\bROOT\\b', linea))>0 or "TORSDOF" in linea or "@<TRIPOS>ATOM" in linea or "@<TRIPOS>BOND" in linea:
		contadorDeModelo+=1;
	linea=linea[:-1]
	if linea!= "":
		get_com()
	if contadorDeModelo == 2 and nAtom == 0:
		contadorDeModelo = 1
f.close()
valoresCoordenadas[0] = round (valoresCoordenadas[0] / nAtom ,3);
valoresCoordenadas[1] = round (valoresCoordenadas[1] / nAtom ,3);
valoresCoordenadas[2] = round (valoresCoordenadas[2] / nAtom ,3);
print (str(valoresCoordenadas[0])+":"+str(valoresCoordenadas[1])+":"+str(valoresCoordenadas[2]))


