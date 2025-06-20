#!/usr/bin/env bash
execute_script()
{
        unset DISPLAY
        TAG=`echo $(basename $BASH_SOURCE)`
        if [ ${option} == "VS" ];then
             path=$PWD
             cd ${path_external_sw}openeye/omega/
            prefix=$( basename "${out_molec}" | sed 's/_no_target//g' )
             if [ "${target}" != "no_target" ]; then
                 confs="-maxconfs ${target}"
             else
                 confs=""
             fi
             execute "./omega2 -in ${CWD}${query} -out ${prefix}.mol2 ${confs} &> ${out_aux}.ucm"
             mkdir -p ${folder_experiment}/molecules/${prefix}
             mv ${prefix}* ${folder_experiment}/molecules/${prefix}
             cd $path
        else
                echo "OM only works with VS technique"
                exit
        fi
}