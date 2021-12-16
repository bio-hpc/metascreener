#!/usr/bin/env bash
#
#	Check if parameter exist in template
#

source ${path_login_node}/special_params.sh

read_template_params $software

for i in `seq 1 $contadorFile`;do
	IFS='::' read -ra ADDR <<< "${file[$i]}"

	if [ ${ADDR[0]} != "-" ];then
		if [[ ${ADDR[4]} !=  *$allComand* ]];then
			if [[ "$optAdicionals" != *${ADDR[4]}* ]];then
				if [ "${ADDR[2]}" == "Y" ];then
					optAdicionals="$optAdicionals ${ADDR[4]} ${ADDR[0]} "

				else
					optAdicionals="$optAdicionals ${ADDR[4]} "
				fi
			fi
		fi
	fi
done
echo "$optAdicionals" > ${folder_templates_jobs}parameter_aux.txt
debugB "_________________________________________Extra Params________________________________________"
debugB ""
debugB "createParams.sh  $optAdicionals"
debugB ""
