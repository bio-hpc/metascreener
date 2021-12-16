#!/bin/bash
echo "Runs:"
total=()
for job in $(ls $1/*-*.err)
do
  lines=$(cat $job | grep -E '([0-9]{2}:){2}[0-9]{2}')
  time=()
  for word in $lines
  do
     if [[ -n $(echo ${word} | grep -E '([0-9]{2}:){2}[0-9]{2}') ]]; then
     	time+=( $word )
     fi
  done
  total+=($((($(date -d ${time[1]} "+%s") - $(date -d ${time[0]} "+%s")) )))
  echo "- $(basename ${job} .err)-- ${total[-1]} s"
done

sum=0
for i in ${total[@]}; do
  let sum+=$i
done

echo "Total: ${sum}"

if [[ $1 != *"_LS_"* ]]; then
  echo -e "\nget_histogram_picture:"
  cat $1/post.out | grep -E '[0-9]+.[0-9]+ s' | sed s/"End "//g
fi

sum_h=$(cat $1/post.out | grep "Finished experiment" | grep -Eo '[0-9]*\.?[0-9]*')

IFS=$'\n'
max=$(echo "${total[*]}" | sort -nr | head -n1)

echo -e "\n Real time:" $(echo $max + $sum_h | bc)

echo -e "\n CPU time:" $(echo $sum + $sum_h | bc)
