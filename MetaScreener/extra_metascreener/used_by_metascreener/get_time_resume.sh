#!/bin/bash
echo "Runs:"
total=()
for job in $1/*-*.err
do
  lines=$(grep -E '([0-9]{2}:){2}[0-9]{2}' "$job")
  time=()
  for word in $lines
  do
    if [[ -n $(echo "${word}" | grep -E '([0-9]{2}:){2}[0-9]{2}') ]]; then
      time+=( "$word" )
    fi
  done
  total+=( $(( ($(date -d "${time[1]}" "+%s") - $(date -d "${time[0]}" "+%s")) )) )
  echo "- $(basename "${job}" .err)-- ${total[-1]} s"
done

sum=0
for i in "${total[@]}"; do
  (( sum += i ))
done

echo "Total: ${sum}"

if [[ $1 != *"_LS_"* ]]; then
  echo -e "\nget_histogram_picture:"
  grep -E '[0-9]+.[0-9]+ s' "$1/post.out" | sed s/"End "//g
fi

sum_h=$(grep "Finished experiment" "$1/post.out" | grep -Eo '[0-9]*\.?[0-9]*')

IFS=$'\n'
max=$(echo "${total[*]}" | sort -nr | head -n1)

# Use awk for floating-point arithmetic
real_time=$(awk "BEGIN {print $max + $sum_h}")
cpu_time=$(awk "BEGIN {print $sum + $sum_h}")

echo -e "\n Real time:" "$real_time"
echo -e "\n CPU time:" "$cpu_time"
