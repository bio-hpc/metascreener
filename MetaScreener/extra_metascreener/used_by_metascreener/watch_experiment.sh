#!/usr/bin/env bash
# Sample a MetaScreener run while it is in the queue and leave a summary.
#
# Tracks, once a minute by default:
#   - running, pending and completing Slurm tasks, and the busiest node
#   - inodes and bytes of the experiment directory
#   - task tars written against packed/expected_tasks
#   - the largest local stage, if tasks appended packed/stage_inodes.txt
#
# When the array and the histogram leave the queue, sacct adds states,
# elapsed time, MaxRSS and the node count.
#
#   watch_experiment.sh --submit --experiment DIR --array JOBID \
#       [--histogram JOBID] [--partition main] [--time 7-00:00:00] \
#       [--interval 60] [--throttle 20]
#
# The summary is rewritten on every sample, so it already has the peaks if
# the watcher is cancelled. It is written to DIR/watch/summary.txt.

set -uo pipefail

interval=60
partition="main"
wall="7-00:00:00"
mem="1G"
account=""
submit=0
once=0
self_test=0
experiment=""
array_id=""
hist_id=""
throttle=""

usage() {
  cat <<'EOF'
Uso:
  watch_experiment.sh --experiment DIR --array JOBID [opciones]

Opciones:
  --histogram JOBID   Job del template_get_histogram. Si se omite, solo se sigue el array.
  --interval SEG      Segundos entre muestras. Por defecto 60.
  --throttle N        Tope de tareas simultáneas (array_throttle). Sirve para contar
                      cuánto tiempo el array estuvo en ese tope.
  --submit            Envía este mismo script como job de Slurm (1 CPU, 1 G).
  --partition NOMBRE  Partición del job vigilante. Por defecto main.
  --time HH:MM:SS     Tiempo del job vigilante. Por defecto 7-00:00:00.
  --mem MEM           Memoria del job vigilante. Por defecto 1G.
  --account CUENTA    Cuenta de Slurm, si el clúster la exige.
  --once              Una muestra y el resumen, sin esperar a que acaben los jobs.
  --self-test         Comprueba el cálculo de picos con un experimento ficticio.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --experiment) experiment=$2; shift 2 ;;
    --array) array_id=$2; shift 2 ;;
    --histogram) hist_id=$2; shift 2 ;;
    --interval) interval=$2; shift 2 ;;
    --throttle) throttle=$2; shift 2 ;;
    --partition) partition=$2; shift 2 ;;
    --time) wall=$2; shift 2 ;;
    --mem) mem=$2; shift 2 ;;
    --account) account=$2; shift 2 ;;
    --submit) submit=1; shift ;;
    --once) once=1; shift ;;
    --self-test) self_test=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Opción desconocida: $1" >&2; usage >&2; exit 2 ;;
  esac
done

die() { echo "ERROR: $*" >&2; exit 1; }

count_inodes() {
  local out
  out=$(du -s --inodes "$1" 2>/dev/null) || out=""
  if [ -n "$out" ]; then
    printf '%s\n' "$out" | awk '{print $1; exit}'
  else
    find "$1" 2>/dev/null | wc -l | tr -d ' '
  fi
}

count_bytes() {
  du -s -B1 "$1" 2>/dev/null | awk '{print $1; exit}'
}

fs_inodes() {
  df -Pi "$1" 2>/dev/null | awk 'NR==2 {print $3, $4}'
}

stage_peak() {
  local file=$1
  [ -f "$file" ] || { echo 0; return; }
  awk 'NF>=3 && $3+0>m {m=$3+0} END {print m+0}' "$file"
}

task_tars() {
  find "$1/packed" -maxdepth 1 -name 'task_*.tar' -type f 2>/dev/null | wc -l | tr -d ' '
}

expected_tasks() {
  local file=$1/packed/expected_tasks
  if [ -f "$file" ]; then
    tr -d '[:space:]' < "$file"
  else
    echo "?"
  fi
}

# squeue -r expands the array. A missing job is an empty sample, not an error.
queue_snapshot() {
  local ids=$1 raw
  if ! raw=$(timeout 30 squeue -h -r -j "$ids" -o '%T|%N' 2>/dev/null); then
    raw=""
  fi
  printf '%s\n' "$raw" | awk -F'|' '
    NF < 2 || $0 ~ /^ *$/ { next }
    { state=$1; node=$2; count[state]++
      if (state=="RUNNING" && node!="" && node!="(null)" && node!="None") node_n[node]++
    }
    END {
      r=count["RUNNING"]+0; p=count["PENDING"]+0; c=count["COMPLETING"]+0
      o=0; for (s in count) if (s!="RUNNING" && s!="PENDING" && s!="COMPLETING") o+=count[s]
      m=0; for (n in node_n) if (node_n[n]>m) m=node_n[n]
      printf "%d %d %d %d %d\n", r, p, c, o, m
    }'
}

write_summary() {
  local samples=$1 stage_file=$2 out=$3
  local exp_n tar_n
  exp_n=$(expected_tasks "$experiment")
  tar_n=$(task_tars "$experiment")
  awk -v stage="$(stage_peak "$stage_file")" -v expected="$exp_n" -v tars="$tar_n" \
      -v throttle="$throttle" -v interval="$interval" -v experiment="$experiment" \
      -v array_id="$array_id" -v hist_id="${hist_id:-}" '
    NR==1 { next }
    NF < 10 { next }
    { n++; if ($2>mr) mr=$2; if ($3>mp) mp=$3; if ($4>mc) mc=$4; if ($5>mn) mn=$5
      if ($6>mi) { mi=$6; mi_epoch=$1 } if ($7>mb) { mb=$7; mb_epoch=$1 }
      if (throttle+0>0 && $2+0>=throttle+0) sat++
      last_r=$2; last_p=$3; last_i=$6; last_b=$7; last_fsu=$10; last_fsf=$11
    }
    function stamp(epoch,    cmd, line) {
      if (epoch+0==0) return "-"
      cmd = "date -d @" epoch " +%Y-%m-%d\\ %H:%M:%S"
      if ((cmd | getline line) > 0) { close(cmd); return line }
      return epoch
    }
    function human(bytes,    u, v) {
      v=bytes+0; u="B"
      if (v>=1024) { v/=1024; u="K" }
      if (v>=1024) { v/=1024; u="M" }
      if (v>=1024) { v/=1024; u="G" }
      if (v>=1024) { v/=1024; u="T" }
      return sprintf("%.1f %s", v, u)
    }
    END {
      if (n==0) { print "Sin muestras."; exit }
      print "Experimento: " experiment
      print "Array: " array_id (hist_id!="" ? "    Histograma: " hist_id : "    Histograma: (no indicado)")
      print "Muestras: " n "  (cada " interval " s)"
      print ""
      print "Jobs simultáneos"
      print "  Pico RUNNING: " mr+0
      print "  Pico PENDING: " mp+0
      print "  Pico COMPLETING: " mc+0
      print "  Pico en un mismo nodo: " mn+0
      if (throttle+0>0) printf "  Muestras en el tope de %d: %d (unos %d min)\n", throttle+0, sat+0, int((sat*interval)/60)
      print "  Última muestra: " last_r+0 " RUNNING, " last_p+0 " PENDING"
      print ""
      print "Ficheros del experimento (inodos del árbol, ficheros y directorios)"
      print "  Pico: " mi+0 "  en " stamp(mi_epoch)
      print "  Última muestra: " last_i+0 "  (" human(last_b) ")"
      print "  Pico de bytes: " human(mb) "  en " stamp(mb_epoch)
      print "  Tars de tarea ahora: " tars " / " expected
      print "  Pico del stage local (packed/stage_inodes.txt): " stage+0
      if (last_fsu!="" && last_fsu!="-") print "  Inodos usados en el sistema de ficheros (df, incluye a otros usuarios): " last_fsu " usados, " last_fsf " libres"
    }
  ' "$samples" > "$out"
}

append_sacct() {
  local out=$1 ids raw
  ids=$array_id
  [ -n "$hist_id" ] && ids="$ids,$hist_id"
  if ! raw=$(timeout 60 sacct -P -n --delimiter='|' -j "$ids" \
      --format=JobID,State,ElapsedRaw,MaxRSS,NNodes,AllocCPUS,ExitCode,NodeList,Submit,Start 2>/dev/null); then
    printf '\nSlurm no devolvió sacct para %s.\n' "$ids" >> "$out"
    return
  fi
  printf '%s\n' "$raw" | awk -F'|' -v array_id="$array_id" -v hist_id="$hist_id" '
    function rss(s,    n, u) {
      if (s=="" ) return 0
      n=s+0; u=substr(s, length(s), 1)
      if (u=="K") return n*1024
      if (u=="M") return n*1024*1024
      if (u=="G") return n*1024*1024*1024
      return n
    }
    function human(bytes,    u, v) {
      v=bytes+0; u="B"
      if (v>=1024) { v/=1024; u="K" }
      if (v>=1024) { v/=1024; u="M" }
      if (v>=1024) { v/=1024; u="G" }
      return sprintf("%.1f %s", v, u)
    }
    function base(s) { sub(/ .*/, "", s); return s }
    function is_task(id) { return id ~ ("^" array_id "_[0-9]+$") }
    {
      id=$1; st=base($2); el=$3+0; mem=rss($4); nodes=$8; subm=$9; start=$10
      if (is_task(id)) {
        tasks++
        state[st]++
        if (el>0) { elapsed[++ne]=el; if (el>max_el) { max_el=el; max_el_id=id }
          if (min_el==0 || el<min_el) min_el=el; sum_el+=el }
        if (nodes!="" && nodes!="None" && nodes!="(null)") nodelist[nodes]=1
      }
      # Slurm guarda MaxRSS en el paso .batch, no en la línea de la tarea.
      if (id ~ ("^" array_id "_[0-9]+\\.batch$") && mem>max_rss) {
        max_rss=mem; max_rss_id=id
      }
      if (hist_id!="" && id==hist_id) {
        hist_state=st; hist_el=el; hist_exit=$7
      }
      if (hist_id!="" && (id==hist_id ".batch") && mem>hist_rss) hist_rss=mem
    }
    function hhmm(sec,    h, m, s) {
      sec=int(sec+0); h=int(sec/3600); m=int((sec%3600)/60); s=sec%60
      return sprintf("%d:%02d:%02d", h, m, s)
    }
    END {
      print ""
      print "Cierre según sacct"
      if (tasks==0) { print "  El array todavía no tiene tareas registradas."; exit }
      print "  Tareas del array: " tasks+0
      nst=0
      for (s in state) order[++nst]=s
      # Stable-enough: print the states that matter first, then the rest.
      split("COMPLETED FAILED TIMEOUT OUT_OF_MEMORY CANCELLED NODE_FAIL", pref, " ")
      seen_pref=""
      for (i=1;i<=6;i++) if (state[pref[i]]+0>0) print "  " pref[i] ": " state[pref[i]]
      for (s in state) {
        keep=0
        for (i=1;i<=6;i++) if (s==pref[i]) keep=1
        if (!keep) print "  " s ": " state[s]
      }
      if (ne>0) {
        asort(elapsed)
        mid=elapsed[int((ne+1)/2)]
        if (ne%2==0) mid=int((elapsed[ne/2]+elapsed[ne/2+1])/2)
        print "  Duración min / mediana / max: " hhmm(min_el) " / " hhmm(mid) " / " hhmm(max_el) "  (max en " max_el_id ")"
      }
      if (max_rss>0) print "  MaxRSS máximo: " human(max_rss) "  (" max_rss_id ")"
      nn=0; for (n in nodelist) nn++
      print "  NodeList distintos en las tareas: " nn " (un rango tipo nodo[01-04] cuenta como uno; scontrol, abajo, los abre)"
      if (hist_id!="") {
        if (hist_state=="") print "  Histograma: sin registro en sacct"
        else print "  Histograma: " hist_state "  duración " hhmm(hist_el) "  exit " hist_exit "  MaxRSS " (hist_rss>0 ? human(hist_rss) : "sin dato")
      }
    }
  ' >> "$out"

  if command -v scontrol >/dev/null 2>&1; then
    local hosts
    hosts=$(printf '%s\n' "$raw" | awk -F'|' -v array_id="$array_id" '
      $1 ~ ("^" array_id "_[0-9]+$") && $8!="" && $8!="None" { print $8 }
    ' | sort -u | while read -r spec; do
      timeout 20 scontrol show hostname "$spec" 2>/dev/null || printf '%s\n' "$spec"
    done | sort -u | wc -l | tr -d ' ')
    printf '  Nodos distintos (scontrol): %s\n' "$hosts" >> "$out"
  fi
}

append_failures() {
  local out=$1 n=0 tar
  [ -d "$experiment/packed" ] || return 0
  for tar in "$experiment"/packed/task_*.tar; do
    [ -f "$tar" ] || continue
    n=$((n + $(tar -xOf "$tar" failed.jsonl 2>/dev/null | grep -c . || true)))
  done
  printf '  Ligandos anotados en failed.jsonl: %s\n' "$n" >> "$out"
}

sample_once() {
  local ids snap running pending completing other max_node inodes bytes tars stage fs
  ids=$array_id
  [ -n "$hist_id" ] && ids="$ids,$hist_id"
  snap=$(queue_snapshot "$ids")
  # shellcheck disable=SC2086
  read -r running pending completing other max_node <<< ${snap:-0 0 0 0 0}
  inodes=$(count_inodes "$experiment")
  bytes=$(count_bytes "$experiment")
  tars=$(task_tars "$experiment")
  stage=$(stage_peak "$experiment/packed/stage_inodes.txt")
  fs=$(fs_inodes "$experiment")
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date +%s)" "${running:-0}" "${pending:-0}" "${completing:-0}" "${max_node:-0}" \
    "${inodes:-0}" "${bytes:-0}" "${tars:-0}" "${stage:-0}" ${fs:-"- -"} \
    >> "$samples"
  write_summary "$samples" "$experiment/packed/stage_inodes.txt" "$summary"
  printf '%s\n' "$running $pending $completing"
}

queue_busy() {
  local ids n
  ids=$array_id
  [ -n "$hist_id" ] && ids="$ids,$hist_id"
  n=$(timeout 30 squeue -h -j "$ids" 2>/dev/null | wc -l | tr -d ' ')
  [ "${n:-0}" -gt 0 ]
}

# True when every array task, and the histogram if one was given, has a
# terminal state in sacct. A failed squeue poll is not enough to stop.
jobs_finished() {
  local ids=$array_id
  [ -n "$hist_id" ] && ids="$ids,$hist_id"
  timeout 60 sacct -n -X -P --delimiter='|' -j "$ids" --format=JobID,State 2>/dev/null \
    | awk -F'|' -v array_id="$array_id" -v hist="$hist_id" '
      {
        id=$1; st=$2; sub(/ .*/, "", st)
        live = (st=="PENDING" || st=="RUNNING" || st=="COMPLETING" || st=="CONFIGURING" || st=="REQUEUED" || st=="SUSPENDED")
        if (id ~ ("^" array_id "_[0-9]+$")) { array_n++; if (live) array_live=1 }
        if (hist!="" && id==hist) { hist_n++; if (live) hist_live=1 }
      }
      END {
        ok = (array_n>0 && !array_live)
        if (hist != "") ok = ok && hist_n>0 && !hist_live
        exit !ok
      }
    '
}

run_self_test() {
  local tmp=$1
  experiment=$tmp/exp
  array_id=1
  interval=60
  throttle=2
  mkdir -p "$experiment/packed" "$experiment/watch" "$experiment/molecules"
  printf 'a\n' > "$experiment/ligands.list"
  printf '2\n' > "$experiment/packed/expected_tasks"
  : > "$experiment/packed/task_00000.tar"
  printf '1 t 10\n2 t 40\n3 t 25\n' > "$experiment/packed/stage_inodes.txt"
  samples=$experiment/watch/samples.tsv
  summary=$experiment/watch/summary.txt
  printf 'epoch\trunning\tpending\tcompleting\tmax_on_node\tinodes\tbytes\ttask_tars\tstage_peak\tfs_iused\tfs_ifree\n' > "$samples"
  printf '1000\t2\t5\t0\t1\t10\t1000\t0\t10\t1\t9\n' >> "$samples"
  printf '1060\t4\t1\t0\t3\t80\t9000\t1\t40\t2\t8\n' >> "$samples"
  write_summary "$samples" "$experiment/packed/stage_inodes.txt" "$summary"
  grep -q 'Pico RUNNING: 4' "$summary" || die "pico de jobs"
  grep -q 'Pico en un mismo nodo: 3' "$summary" || die "pico por nodo"
  grep -q 'Pico: 80' "$summary" || die "pico de inodos"
  grep -q 'stage local.*: 40' "$summary" || die "pico de stage"
  grep -q 'tope de 2: 2' "$summary" || die "tiempo en el tope"
  echo "self-test ok"
}

submit_self() {
  local script dir extra=()
  script=$(readlink -f "$0")
  experiment=$(readlink -f "$experiment")
  dir=$experiment/watch
  mkdir -p "$dir"
  [ -n "$account" ] && extra+=(--account "$account")
  sbatch --job-name=ms_watch --cpus-per-task=1 --mem="$mem" --time="$wall" \
    --partition="$partition" --chdir="$experiment" \
    --output="$dir/watch-%j.out" --error="$dir/watch-%j.err" \
    "${extra[@]}" \
    "$script" --experiment "$experiment" --array "$array_id" \
    ${hist_id:+--histogram "$hist_id"} --interval "$interval" \
    ${throttle:+--throttle "$throttle"}
}

if [ "$self_test" = 1 ]; then
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  run_self_test "$tmp"
  exit 0
fi

[ -n "$experiment" ] || die "--experiment es obligatorio"
[ -d "$experiment" ] || die "no existe el experimento: $experiment"
[ -n "$array_id" ] || die "--array es obligatorio"
experiment=$(readlink -f "$experiment")
[[ "$interval" =~ ^[0-9]+$ ]] || die "--interval tiene que ser un número de segundos"

watch_dir=$experiment/watch
mkdir -p "$watch_dir"
samples=$watch_dir/samples.tsv
summary=$watch_dir/summary.txt

if [ "$submit" = 1 ]; then
  submit_self
  exit 0
fi

if [ ! -f "$samples" ]; then
  printf 'epoch\trunning\tpending\tcompleting\tmax_on_node\tinodes\tbytes\ttask_tars\tstage_peak\tfs_iused\tfs_ifree\n' > "$samples"
fi

echo "Vigilando $experiment array=$array_id histograma=${hist_id:-ninguno} cada ${interval}s" >&2
echo "Resumen: $summary" >&2

sample_once >/dev/null
if [ "$once" = 1 ]; then
  append_sacct "$summary" || true
  append_failures "$summary" || true
  echo "Muestra escrita en $summary" >&2
  exit 0
fi

empty_streak=0
while true; do
  sleep "$interval"
  sample_once >/dev/null || true
  if queue_busy; then
    empty_streak=0
  elif jobs_finished; then
    empty_streak=$((empty_streak + 1))
    if [ "$empty_streak" -ge 2 ]; then
      break
    fi
  else
    empty_streak=0
  fi
done

sample_once >/dev/null || true
append_sacct "$summary" || true
append_failures "$summary" || true
echo "Ejecución fuera de la cola. Resumen: $summary" >&2
