#!/bin/bash
# Toy VS with a tar ligand library: plumbing test, then a real AD run and a real LF run.
# The library is four copies of the repository's GLA ligand. Scores will match;
# what is checked is that every ligand is docked, that GPFS only keeps the top
# poses as loose files, and that the final archive is still a tar.gz.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
WORK="$ROOT/tests/vs_tar/work"
IMAGE="$ROOT/singularity/metascreener.simg"
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
only="${1:-all}"

if [ "$only" != "lf" ]; then
echo "== index / materialize (host $PY) =="
"$PY" "$ROOT/tests/vs_tar/test_packed_store.py"

if [ ! -f "$IMAGE" ]; then
  echo "ERROR: missing $IMAGE" >&2
  exit 1
fi

echo "== index / materialize (container python) =="
singularity exec --bind /home/ "$IMAGE" python "$ROOT/tests/vs_tar/test_packed_store.py"

echo "== slice extraction =="
slice=$(mktemp -d "${TMPDIR:-/tmp}/ms_slice.XXXXXX")
mkdir -p "$slice/src" "$slice/packed"
for name in L_a L_b L_c L_d; do
  echo "$name" > "$slice/src/${name}.pdbqt"
done
tar -cf "$slice/lib.tar" -C "$slice/src" .
tar -tf "$slice/lib.tar" | grep -E '\.pdbqt$' | LC_ALL=C sort > "$slice/ligands.list"
# shellcheck disable=SC1091
source "$ROOT/MetaScreener/cluster_nodes/tar_runtime.sh"
MS_QUERY_TAR="$slice/lib.tar"
MS_LIGANDS_LIST="$slice/ligands.list"
MS_EXT_QUERY=".pdbqt"
MS_EXPERIMENT="$slice"
MS_PACKED_PY="$ROOT/MetaScreener/analyze_results/Get_histogram/PackedStore.py"
contIni=2
contFin=4
ms_tar_begin
trap - EXIT INT TERM
test "$(find "$MS_STAGE/ligs" -maxdepth 1 -type f -name '*.pdbqt' | wc -l | tr -d ' ')" = "2"
rm -rf "$MS_STAGE" "$slice"
echo "slice extraction ok"
fi

build_library() {
  local ext="$1" dest="$2" src="$3"
  local dir
  dir=$(mktemp -d)
  cp "$src" "$dir/GLA_a.${ext}"
  cp "$src" "$dir/GLA_b.${ext}"
  cp "$src" "$dir/GLA_c.${ext}"
  cp "$src" "$dir/GLA_d.${ext}"
  tar -cf "$dest" -C "$dir" .
  rm -rf "$dir"
  echo "library $dest ($(tar -tf "$dest" | grep -c "\.${ext}$") ligands)"
}

check_run() {
  local dir="$1" ext="$2" nlig="$3" ntop="$4" tgz="$5"
  local ntars nidx nene nmol nsoft nout nrows
  ntars=$(find "$dir/packed" -name 'task_*.tar' | wc -l | tr -d ' ')
  [ "$ntars" = "2" ]
  nidx=0
  for archive in "$dir"/packed/task_*.tar; do
    members=$(tar -tf "$archive")
    case "$members" in
      *"index.jsonl"*) ;;
      *) echo "missing index.jsonl in $archive" >&2; exit 1;;
    esac
    case "$members" in
      *molecules/*) ;;
      *) echo "missing molecules in $archive" >&2; exit 1;;
    esac
    case "$members" in
      *energies/*) ;;
      *) echo "missing energies in $archive" >&2; exit 1;;
    esac
    nidx=$((nidx + $(tar -xOf "$archive" index.jsonl | grep -c . || true)))
  done
  [ "$nidx" = "$nlig" ]
  nene=$(find "$dir/energies" -name '*.json' | wc -l | tr -d ' ')
  nmol=$(find "$dir/molecules" -type f -name "*.${ext}" | wc -l | tr -d ' ')
  nsoft=$(find "$dir/soft_out" -type f | wc -l | tr -d ' ')
  nout=$(find "$dir/output" -type f | wc -l | tr -d ' ')
  [ "$nene" = "$ntop" ]
  [ "$nmol" = "$ntop" ]
  [ "$nsoft" = "0" ]
  [ "$nout" = "0" ]
  [ "$(grep -c . "$dir/packed/all_scores.txt" | tr -d ' ')" = "$nlig" ]
  nrows=$(($(grep -c . "$dir/Results_scoring.csv") - 1))
  [ "$nrows" = "$nlig" ]
  [ "$(find "$dir/results/best_scores" -type f -name "VS_*.${ext}" | wc -l | tr -d ' ')" -ge 1 ]
  archive_list=$(tar -tzf "$tgz")
  case "$archive_list" in
    *packed/task_*) ;;
    *) echo "final archive has no task tars" >&2; exit 1;;
  esac
  case "$archive_list" in
    *Results_scoring.csv*) ;;
    *) echo "final archive has no Results_scoring.csv" >&2; exit 1;;
  esac
  echo "OK $dir: ${ntars} task tars, ${nidx} packed poses, ${ntop} loose poses, archive $(basename "$tgz")"
}

run_vs() {
  local software="$1" target="$2" library="$3" x="$4" y="$5" z="$6" out="$7"
  rm -rf "$ROOT/$out" "$ROOT/$(basename "$out").tar.gz"
  echo "== VS $software =="
  bash "$ROOT/ms.sh" -o VS -s "$software" -t "$target" -q "$library" \
    -x "$x" -y "$y" -z "$z" -ij 2 -se y -hi y -qu main -nj "toy_tar_${software}" \
    -d "$out" -rf 1 -rb 1
  local tgz="$ROOT/$(basename "$out").tar.gz"
  [ -f "$tgz" ]
  mv "$tgz" "$WORK/"
}

if [ "$only" != "lf" ]; then
  rm -rf "$WORK"
  mkdir -p "$WORK"
  build_library pdbqt "$WORK/ad_ligands.tar" "$ROOT/queries/test/GLA.pdbqt"
  build_library mol2 "$WORK/lf_ligands.tar" "$ROOT/queries/test/GLA.mol2"
fi
mkdir -p "$WORK"
if [ ! -f "$WORK/lf_ligands.tar" ]; then
  build_library mol2 "$WORK/lf_ligands.tar" "$ROOT/queries/test/GLA.mol2"
fi

# -t and -q stay relative to the repository. MetaScreener prefixes them with
# the working directory; an absolute path would be prefixed twice.
if [ "$only" != "lf" ]; then
  run_vs AD "targets/test/1le0.pdbqt" "tests/vs_tar/work/ad_ligands.tar" -4.054 8.999 -2.299 "tests/vs_tar/work/ad_run"
  check_run "$WORK/ad_run" pdbqt 4 2 "$WORK/ad_run.tar.gz"
fi

run_vs LF "targets/test/1le0.mol2" "tests/vs_tar/work/lf_ligands.tar" -3 10 1 "tests/vs_tar/work/lf_run"
check_run "$WORK/lf_run" mol2 4 2 "$WORK/lf_run.tar.gz"

echo "Toy AD and LF tar runs finished."
