import re,sys
original=open(sys.argv[1])
cargas=[];c1=0
for linea in original:
    if re.search("@<TRIPOS>ATOM",linea):
        c1=1
    elif re.search("@<TRIPOS>BOND",linea):
        c1=0
    elif c1==1:

        linea=re.sub(' +', ' ',linea).strip()
        linea=linea.split(" ")
        carga=linea[-1]
        cargas.append(carga)

modificada=open(sys.argv[2]);nombre_nuevo=sys.argv[2][:-5]+"_v2.mol2"
modificada_2=open(nombre_nuevo,"w+")
texto=""
c1=0;i=0
for linea in modificada:
    if re.search("@<TRIPOS>ATOM",linea):
        c1=1
        texto=texto+linea
    elif re.search("@<TRIPOS>BOND",linea):
        c1=0
        texto=texto+linea
    elif c1==1 and len(linea)>1:
        carga=cargas[i];x=len(carga)+1
        texto=texto+linea[:-x]+carga+"\n"
        i=i+1  
    else:
        texto=texto+linea
modificada_2.write(texto)
modificada_2.close()