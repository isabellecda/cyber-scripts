#!/bin/bash

# Input params
host="$1"
user="$2"    
pass="$3"

# Colors
RED='\033[1;31m'
YELLOW='\033[1;33m'
GRAY='\033[0;37m'
RST='\033[0m'

# Check host
if [ -z "$host" ]
then
	echo "Usage: $0 host [user] [pass]"
	echo "Default user and password is 'anon'"
	exit 1
fi

# Check user name and password
if [ -z "$user" ] ; then user="anon" ; fi
if [ -z "$pass" ] ; then pass="anon" ; fi

# smbclient
smbclient=$(which smbclient)

shareList=$($smbclient -g -t 2 -L "$host" -U "${user}%${pass}" 2>/dev/null | awk -F'|' '$1 == "Disk" {print $2}')

# Write file
cd "${TMPDIR:-/tmp}"
touch tmp_$$.tmp  

for share in $shareList
do
	if $smbclient "//$host/$share/" -U "${user}%${pass}" -c "lcd" >/dev/null 2>&1
	then
		# Current dir
		if $smbclient "//$host/$share/" -U "${user}%${pass}"  -c "put tmp_$$.tmp ; rm tmp_$$.tmp" >/dev/null 2>&1
		then
			echo -en "${RED}WRITE\t"
			echo -n ": ${share} : ."
			echo -e "${RST}"
		else
			echo -en "${YELLOW}READ\t"
			echo -n ": ${share} : ."
			echo -e "${RST}"
		fi

		# Recursive dir
		$smbclient "//$host/$share/" -U "${user}%${pass}"  -c "recurse;dir" | egrep ^'\\' 2>/dev/null | 	while IFS= read -r line
		do
			if smbclient "//$host/$share/" -U "${user}%${pass}" -c "cd $line; put tmp_$$.tmp ; rm tmp_$$.tmp" >/dev/null 2>&1
			then
				echo -en "${RED}WRITE\t"
				echo -n ": ${share} : ${line}"
				echo -e "${RST}"

			else
				echo -en "${YELLOW}READ\t"
				echo -n ": ${share} : ${line}"
				echo -e "${RST}"
			fi
		done
	else
		echo -en "${GRAY}NONE\t"
		echo -n ": ${share}"
		echo -e "${RST}"
	fi
done

rm -f tmp_$$.tmp

exit
