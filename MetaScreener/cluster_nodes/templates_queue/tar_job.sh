#!/usr/bin/env bash
# Emits, into the job script being generated, the tar-library staging block.
# Sourced by codigo.sh and codigo_array.sh while the submission script is built.

_tar_append() {
  printf '%s\n' "$1" >> "$name_template_job"
}

_tar_singularity() {
  # $1 ini token, $2 fin token, $3 -q value, $4 extra --bind text (may be empty)
  _tar_append "singularity exec ${singularity_prefix} --bind ${bind} ${4} ${singularity_image} ${path_cluster_nodes}techniques/baseTechniques.sh -c ${CWD} -d ${folder_experiment} -s ${software} -t ${target} -q ${3} -x ${x} -y ${y} -z ${z} -nt ${name_target} -o ${option} -in ${1} -fn ${2} -nc ${numPoses} -fl ${flexFile} -nj ${NombreJob} -fx ${flex} -na ${num_amino_acid} -ch ${chain} -nq ${name_query} -de ${debug} -td ${time_experiment} -co ${cores} -gpu ${GPU} -mm ${mem} -tr ${torsion} -sc ${scoreCorte} -grid ${grid} -EXP ${ext_target} -EXL ${ext_query} -GX ${gridSizeX} -GY ${gridSizeY} -GZ ${gridSizeZ} -nn ${nodos} -lto ${lanzTimeOut} -nj ${name_job} -BE ${bd_exhaustiveness} -BDA ${bd_atom_default}"
}

# mode: fixed (contIni/contFin already known) or runtime (run_task already emitted)
emit_tar_job() {
  local mode="$1"
  local exp extra
  if [ -z "$query_tar" ] || [ -z "$tar_query_rel" ]; then
    echo "ERROR: tar library was not prepared (missing ${query_tar:-archive} or staging path)." >&2
    exit 1
  fi
  if [ "$mode" = "fixed" ]; then
    _tar_append "contIni=${contIni}"
    _tar_append "contFin=${contFin}"
  fi
  _tar_append "MS_QUERY_TAR=\"${query_tar}\""
  _tar_append "MS_LIGANDS_LIST=\"${folder_experiment}ligands.list\""
  _tar_append "MS_EXT_QUERY=\"${ext_query}\""
  _tar_append "MS_EXPERIMENT=\"${folder_experiment%/}\""
  _tar_append "MS_PACKED_PY=\"${CWD}MetaScreener/analyze_results/Get_histogram/PackedStore.py\""
  if [ -n "$stage_dir" ] && [ "$stage_dir" != "N/A" ]; then
    _tar_append "MS_STAGE_ROOT=\"${stage_dir}\""
  fi
  _tar_append "source ${path_cluster_nodes}tar_runtime.sh"
  _tar_append 'ms_tar_begin || exit $?'
  _tar_append 'if [ "$MS_TAR_SKIP" != 1 ]; then'
  exp="${folder_experiment}"
  extra="--bind \"\$MS_STAGE/ligs:${exp}${name_query}\" --bind \"\$MS_STAGE/molecules:${exp}molecules\" --bind \"\$MS_STAGE/energies:${exp}energies\" --bind \"\$MS_STAGE/soft_out:${exp}soft_out\" --bind \"\$MS_STAGE/output:${exp}output\""
  _tar_singularity '0' '"$MS_TAR_NFILES"' "${tar_query_rel}" "$extra"
  _tar_append 'ms_tar_finish $?'
  _tar_append 'fi'
}
