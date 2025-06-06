#!/usr/bin/env bash
if [[ "${software}" == "GN" ]]; then
  echo "export OMP_NUM_THREADS=1 "																			>>$name_template_job
  echo "export MKL_NUM_THREADS=1 "																			>>$name_template_job
  echo "export OPENBLAS_NUM_THREADS=1 "																			>>$name_template_job
fi

echo "echo \"start job\" 1>&2" 																			>>$name_template_job
echo "date +\"%s   %c\" 1>&2"																			>>$name_template_job

bind1=/$(echo ${path_metascreener} | cut -d'/' -f2)/
bind2=/$(echo ${folder_experiment} | cut -d'/' -f2)/

if [ $bind1 == $bind2 ];then
  bind=$bind1
else
  bind=$bind1,$bind2
fi

path_singularity=$(dirname ${path_metascreener})"/singularity/"

singularity_image="${path_singularity}metascreener.simg"
if [[ "${software}" == "EO" ]] ||[[ "${software}" == "RC" ]] || [[ "${software}" == "OM" ]] || [[ "${software}" == "GN" ]] ; then
  singularity_image="${path_singularity}metascreener_22.04.simg"
fi

singularity_prefix=""

if [[ "${software}" == "GN" && "${GPU}" != "N/A" ]]; then
  singularity_prefix+="--nv "
fi

echo $modules_metascreener >>$name_template_job
echo "singularity exec ${singularity_prefix} --bind $bind ${singularity_image} ${path_cluster_nodes}techniques/baseTechniques.sh -c ${CWD} \
-d ${folder_experiment} -s ${software} -t ${target} -q ${query} -x ${x} -y ${y} -z ${z} \
-nt ${name_target} -o ${option} -in ${contIni} -fn ${contFin} \
-nc ${numPoses} -fl ${flexFile} -nj ${NombreJob} -fx ${flex} -na ${num_amino_acid} -ch ${chain} \
-nq ${name_query} -de ${debug} -td ${time_experiment} -co ${cores} -gpu ${GPU} -mm ${mem} -tr ${torsion} \
-sc ${scoreCorte} -grid ${grid} -EXP ${ext_target} -EXL ${ext_query} \
-GX ${gridSizeX} -GY ${gridSizeY} -GZ ${gridSizeZ} -nn  ${nodos} -lto ${lanzTimeOut} \
-nj ${name_job} -BE ${bd_exhaustiveness} -BDA ${bd_atom_default}"		 														>>$name_template_job
echo "mv $name_template_job ${folder_jobs_done}"                                                        >>$name_template_job

echo "echo \"end job\" 1>&2" 																			>>$name_template_job
echo "date +\"%s   %c\" 1>&2" 																			>>$name_template_job	
