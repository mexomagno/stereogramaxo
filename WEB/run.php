<?php 
var_dump($_REQUEST);
var_dump($_FILE);
//$result = system("$cwd/py/ENV/bin/python $cwd/py/sirds.py");
$sirds_path = "/home/mexomagno/Workspace_ext4/stereogramaxo";

$cmd_text = "$sirds_path/ENV/bin/python $sirds_path/sirds.py -d $sirds_path/depth_maps/tiburon.png --dots -w --blur 6 --forcedepth 1 -o out";
$cmd = escapeshellcmd($cmd_text);

# Expect a JSON with results
$script_response = exec($cmd, $cmd_output, $shell_retcode);

$response_data = "";

switch($shell_retcode){
	case 0:
		http_response_code(200);
		$response_data = json_decode($script_response);
		break;
	case 126:
		http_response_code(500);
		$response_data = "Server has permission issues! Fix first";
	default:
		http_response_code(500);
		$response_data = "Unknown error happened on the server"; 
}

// header('Content-Type: application/json');
// echo json_encode($shell_retcode == 0 ? $response_data : array("error" => $response_data));
?>