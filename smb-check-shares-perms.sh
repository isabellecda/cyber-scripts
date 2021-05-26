#!/bin/bash
#
# Credits: https://unix.stackexchange.com/questions/367321/determine-smb-shares-i-have-read-and-or-write-access-to
#
#username="DOMAIN\\USER"    # Double backslash
#password="PASSWORD"        # For demonstration purposes only
#hostname="TARGET_HOST"     # SMB hostname of target

hostname="$1"
username="$2"    
password="$3"


cd "${TMPDIR:-/tmp}"
touch tmp_$$.tmp           # Required locally to copy to target

smbclient -L "$hostname" -g -A <( echo "username=$username"; echo "password=$password" ) 2>/dev/null |
    awk -F'|' '$1 == "Disk" {print $2}' |
    while IFS= read -r share
    do
        echo -n "Share '$share' : "

        if smbclient "//$hostname/$share/" "$password" -U "$username"-c "dir" >/dev/null 2>&1
        then
            status=READ

            # Try uprating to read/write
            if smbclient "//$hostname/$share/" "$password" -U "$username" -c "put tmp_$$.tmp ; rm tmp_$$.tmp" >/dev/null 2>&1
            then
                status=WRITE
            fi
        else
            status=NONE
        fi

        case "$status" in
            READ) echo "! Read access" ;;
            WRITE) echo "!! Write access" ;;
            *) echo "-" ;;
        esac
    done

rm -f tmp_$$.tmp
