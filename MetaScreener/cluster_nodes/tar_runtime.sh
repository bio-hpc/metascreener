#!/bin/sh
# Runtime helpers for a VS whose ligand library is a tar archive.
# Sourced by the job script (sh). Keep this file POSIX.

ms_tar_begin() {
  MS_TASK_NAME=$(printf 'task_%05d' "$contIni")
  MS_PACKED_DIR="${MS_EXPERIMENT}/packed"
  MS_TAR_SKIP=0
  mkdir -p "$MS_PACKED_DIR"
  if [ -f "${MS_PACKED_DIR}/${MS_TASK_NAME}.tar" ]; then
    echo "tar library: ${MS_TASK_NAME} already packed, skipping" >&2
    MS_TAR_SKIP=1
    return 0
  fi

  MS_STAGE="${TMPDIR:-/tmp}/ms_${SLURM_JOB_ID:-$$}_${contIni}"
  rm -rf "$MS_STAGE"
  mkdir -p "$MS_STAGE/ligs" "$MS_STAGE/molecules" "$MS_STAGE/energies" "$MS_STAGE/soft_out" "$MS_STAGE/output"
  trap 'rm -rf "$MS_STAGE"' EXIT
  trap 'exit 143' INT TERM

  sed -n "$((contIni + 1)),${contFin}p" "$MS_LIGANDS_LIST" > "$MS_STAGE/list"
  if [ ! -s "$MS_STAGE/list" ]; then
    echo "ERROR: empty ligand slice for ${MS_TASK_NAME} (${contIni}-${contFin})" >&2
    return 1
  fi
  # Flatten members so the docking loop sees a single directory of ligand files.
  tar -xf "$MS_QUERY_TAR" -C "$MS_STAGE/ligs" -T "$MS_STAGE/list" --transform='s|.*/||' || return 1

  nlist=$(grep -c . "$MS_STAGE/list" || true)
  MS_TAR_NFILES=$(find "$MS_STAGE/ligs" -maxdepth 1 -type f -name "*${MS_EXT_QUERY}" | wc -l)
  MS_TAR_NFILES=$(echo "$MS_TAR_NFILES" | tr -d ' ')
  if [ "$MS_TAR_NFILES" != "$nlist" ]; then
    echo "ERROR: ${MS_TASK_NAME} expected ${nlist} ligands, extracted ${MS_TAR_NFILES}" >&2
    return 1
  fi
  echo "tar library: ${MS_TASK_NAME} extracted ${MS_TAR_NFILES} ligands" >&2
  return 0
}

ms_tar_finish() {
  rc=$1
  njson=$(find "$MS_STAGE/energies" -name '*.json' 2>/dev/null | wc -l)
  njson=$(echo "$njson" | tr -d ' ')
  # A non-zero status with no poses means the task itself failed (the container
  # never really ran). A few ligands inside a task that did run are recorded
  # in failed.jsonl and the tar is still published.
  if [ "$rc" -ne 0 ] && [ "$njson" = "0" ]; then
    echo "ERROR: docking failed (status ${rc}) and produced no poses; ${MS_TASK_NAME} was not packed" >&2
    exit "$rc"
  fi
  if [ "$rc" -ne 0 ]; then
    echo "tar library: docking status ${rc}; packing the poses that did score" >&2
  fi
  py=python3
  command -v python3 >/dev/null 2>&1 || py=python
  "$py" "$MS_PACKED_PY" index \
    --energies "$MS_STAGE/energies" \
    --out "$MS_STAGE/index.jsonl" \
    --ligands "$MS_STAGE/list" || exit 1

  tmp="${MS_PACKED_DIR}/.${MS_TASK_NAME}.tar"
  final="${MS_PACKED_DIR}/${MS_TASK_NAME}.tar"
  rm -f "$tmp"
  tar -cf "$tmp" -C "$MS_STAGE" index.jsonl failed.jsonl molecules energies soft_out output || {
    rm -f "$tmp"
    exit 1
  }
  mv "$tmp" "$final" || exit 1
  echo "tar library: wrote ${final}" >&2
}
