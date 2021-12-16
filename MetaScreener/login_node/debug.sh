#/bin/bash
function debugB
{
	if [ "$debug" != "N/A" ] && [[ $debug -gt 0 ]] ;then
		echo -e ${GREEN}DEBUG:${BLUE} ${1} ${NONE}
	fi
}
#LVL 1
function debugC
{
	if [ "$debug" != "N/A" ] && [[ $debug -gt 3 ]] ;then
		echo -e ${GREEN}DEBUG:${CYAN} ${1} ${NONE}
	fi
}
#LVL 2
function debugBB
{
	if [ "$debug" != "N/A" ] && [[ $debug -gt 0 ]] ;then
		echo -e ${GREEN}DEBUG:${BLUEB} ${1} ${NONE}
	fi
}
#
#lvl 3
function debugP
{
	if [ "$debug" != "N/A" ] && [[ $debug -gt 1 ]] ;then
		echo -e ${GREEN}DEBUG:${PURPLE} ${1} ${NONE}
	fi
}
#LVL 4
function debugBr
{
	if [ "$debug" != "N/A" ] && [[ $debug -gt 2 ]] ;then
		echo -e ${GREEN}DEBUG:${BROWN} ${1} ${NONE}
	fi
}
#LVL 5
function debugY
{
	if [ "$debug" != "N/A" ] && [[ $debug -gt 1 ]] ;then

		echo -e ${GREEN}DEBUG:${YELLOW} ${1} ${NONE}
	fi
}

#ERRORS
function debugR
{
	if [ "$debug" != "N/A" ] && [[ $debug -gt 4 ]] ;then
		echo -e ${REDB}DEBUG:${RED} ${1} ${NONE}
	fi
}
