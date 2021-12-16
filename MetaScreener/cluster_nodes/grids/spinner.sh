#!/usr/bin/env bash
pid=$!
spin='-\|/'
i=0
while kill -0 $pid 2>/dev/null
do
	i=$(( (i+1) %4 ))
	printf "\rGenerate Grid: ${spin:$i:1} "
    sleep .1
done
echo ""