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

# Checks read or write permission
function checkReadWritePerm() {
	local share="$1"
	local tdir="$2"
	local tmpFile="$3"

	if $smbclient "//${host}/${share}/" -U "${user}%${pass}"  -c "cd ${tdir}; put ${tmpFile}; rm ${tmpFile}" >/dev/null 2>&1
	then
		echo -en "${RED}WRITE\t"
		echo -n ": ${share} : ${tdir}"
		echo -e "${RST}"
	else
		echo -en "${YELLOW}READ\t"
		echo -n ": ${share} : ${tdir}"
		echo -e "${RST}"
	fi
}

shareList=$($smbclient -g -t 2 -L "$host" -U "${user}%${pass}" 2>/dev/null | awk -F'|' '$1 == "Disk" {print $2}')

# Write file
tmpFile=tmp_$$.tmp

cd "${TMPDIR:-/tmp}"
touch ${tmpFile}

for share in $shareList
do
	if $smbclient "//${host}/${share}/" -U "${user}%${pass}" -c "lcd" >/dev/null 2>&1
	then
		# Current dir
		checkReadWritePerm "${share}" "." "${tmpFile}"

		# Recursive dir
		$smbclient "//${host}/${share}/" -U "${user}%${pass}"  -c "recurse;dir" | egrep ^'\\' 2>/dev/null | 	while IFS= read -r line
		do
			checkReadWritePerm "${share}" "${line}" "${tmpFile}"
		done
	else
		echo -en "${GRAY}NONE\t"
		echo -n ": ${share}"
		echo -e "${RST}"
	fi
done

rm -f ${tmpFile}

exit
