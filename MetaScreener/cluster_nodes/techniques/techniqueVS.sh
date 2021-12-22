#!/bin/bash

TAG="tecniqueVS"
ctr_queries=0;
query_aux=`basename ${query}`
if [[ $software == "LS"* ]];then
	ini=`expr ${ini} + 1`
	executeTecnique "bash ${path_cluster_nodes}run_software.sh  -c $CWD -q $query  -nq `basename ${query%.*}_${ini}-${fin}`"
fi

for fil in ${CWD}${query}*"$ext_query"; do
	if [ $ctr_queries -ge $ini ] && [ $ctr_queries -lt $fin ];then
	    name_query=${fil##$CWD}
		executeTecnique "bash ${path_cluster_nodes}run_software.sh -c ${CWD} -q ${name_query} -nq ${query_aux}"
	fi
	let ctr_queries=ctr_queries+1
done 




























