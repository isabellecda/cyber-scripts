#!/bin/bash
#
# List permisions in shares
#

# Default depth
depth=20

if [ -z "${1}" ]
then
	echo "Usage: $0 IP [-r/-w/-a]"
	echo " -r: show read permissions"
	echo " -w: show write permissions"
	echo " -a: show all permissions (default)"
	echo ""
	echo "Example:"
	echo "$0 192.168.10.90 -r"
	exit
fi

host="$1"

if [[ "$2" =~ "r" ]]
then
	option="r"
elif [[ "$2" =~ "w" ]]
then
	option="w"
else	
	option=""
fi

while read -r line
do
	first_column=$(echo $line | cut -d" " -f1)
	case "$first_column" in
            .*) echo "$line" ;;
            *${option}*) echo "$line" ;;
            *) ;;#echo "-" ;;
        esac

	#echo .
	
done < <(smbmap -H $host -u anonymous --depth $depth -R)
