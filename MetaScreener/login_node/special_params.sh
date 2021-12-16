#!/usr/bin/env bash

read_template_params()
{
	file=""
	contadorFile=0

	if [ -f ${path_login_node}/templateParams/template${1}.txt ];then
		auxIFS=$IFS
		while read -r line
		do
   			if [[ "$line" != \#* ]] && [[ -n $line ]];then
   				contadorFile=`expr $contadorFile + 1`
				file[$contadorFile]="$line"
			fi
		done < "${path_login_node}/templateParams/template${1}.txt"
		IFS=$auxIFS
	else
		echo "There is no template for this SW "
		exit
	fi
}
