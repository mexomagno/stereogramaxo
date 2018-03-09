<?php 
$HTTP_OK = 200;
$HTTP_BAD_REQUEST = 400;
$HTTP_SERVER_ERROR = 500;

/*
	Send response to client. If response is 200 (success), it has to be a json-decoded string. Else, a simple text
**/
function send_response($HTTP_CODE, $response){
	header("Content-Type: application/json");
	// http_response_code($HTTP_CODE);
	echo json_encode($HTTP_CODE == 200 ? $response : "{'error': '".$response."'}");
	exit;
}

/* Vars to receive:

$_POST
dm_switches: "text" if text, "file" if a file
patterh_switches: "dots" if dot pattern "file" if a file
depthmap_text: OPTIONAL text to use in pattern
dot_probability: Probability of dots
blur: blur amount

$_FILES
depthmap_file: OPTIONAL file for depthmap
pattern_file: OPTIONAL file for pattern

*/
// Validate arguments
$script_args = "";

if ( !isset($_POST) )
	send_response($HTTP_BAD_REQUEST, "You must send request via POST method");
if (!isset($_POST["dm_switches"]) || !isset($_POST["pattern_switches"]))
	send_response($HTTP_BAD_REQUEST, "You must select a depthmap and a pattern mode");
$dm_mode = $_POST["dm_switches"];
if ($dm_mode != "text" && $dm_mode != "file")
	send_response($HTTP_BAD_REQUEST, "Invalid depthmap mode");
if ($dm_mode == "text" && (!isset($_POST["depthmap_text"]) || strlen($_POST["depthmap_text"]) == 0))
	send_response($HTTP_BAD_REQUEST, "You must input some text for a text depthmap");
if ($dm_mode == "file" && (!isset($_FILES) || !isset($_FILES["depthmap_file"])))
	send_response($HTTP_BAD_REQUEST, "You must attach an image for an image depthmap");
// Validated depthmap. Convert to args
if ($dm_mode == "text")
	$script_args = $script_args." -t \"".$_POST["depthmap_text"]."\"";
if ($dm_mode == "file"){
	// TODO: Validate image properties
	$dm_path = "/tmp/".basename($_FILES["depthmap_file"]["name"]);
	// send_response(400, "path to upload dm: ".$dm_path);
	if (!move_uploaded_file($_FILES["depthmap_file"]["tmp_name"], $dm_path))
		send_response($HTTP_SERVER_ERROR, "Could not upload depthmap image");
	$script_args = $script_args." -d \"".$dm_path."\"";
}

$pattern_mode = $_POST["pattern_switches"];
if ($pattern_mode != "dots" && $pattern_mode != "file")
	$send_response($HTTP_BAD_REQUEST, "Invalid pattern mode");
if ($pattern_mode == "file" && (!isset($_FILES) || !isset($_FILES["pattern_file"])))
	$send_response($HTTP_BAD_REQUEST, "You must attach an image for an image pattern");
// Validated pattern. Convert to args
if ($pattern_mode == "file"){
	// TODO: Validate image properties
	$p_file = "/tmp/".basename($_FILES["pattern_file"]["name"]);
	// send_response(400, "path to upload dm: ".$p_file);
	if (!move_uploaded_file($_FILES["pattern_file"]["tmp_name"], $p_file))
		send_response($HTTP_SERVER_ERROR, "Could not upload pattern image");
	$script_args = $script_args." -p \"".$p_file."\"";
}
if ($pattern_mode == "dots")
	$script_args = $script_args." --dots";

// Dot aparition options
if (isset($_POST["dot_probability"]) && is_numeric($_POST["dot_probability"])){
	$float_dp = floatval($_POST["dot_probability"]);
	if ($float_dp < 0 || $float_dp > 100){
		send_response($HTTP_BAD_REQUEST, "Invalid dot probability value");
	}
	$script_args = $script_args." --dot-prob ".($float_dp/100.0);
}
if (isset($_POST["dot_bg_color"])){
	$bg_c = $_POST["dot_bg_color"];
	preg_match("/^([a-fA-F0-9]{3}$|^[a-fA-F0-9]{6})$/", $bg_c, $validity);
	// if (!preg_match('/^([a-fA-F0-9]{3}$|^[a-fA-F0-9]{6})$/', $$bg_c)){
	if (count($validity) == 0){
		send_response($HTTP_BAD_REQUEST, "Invalid background color: '".$bg_c."'");
	}
	$script_args = $script_args." --dot-bg-color ".$bg_c;
}


// Blur
if (isset($_POST["blur"]) && ctype_digit($_POST["blur"])){
	$blur = intval($_POST["blur"]);
	if (0 > $blur || $blur > 100){
		send_response($HTTP_BAD_REQUEST, "Invalid blur value");
	}
	$script_args = $script_args." -b ".$blur;
}

// View mode
$view_mode = "-w";
if (isset($_POST["view_mode"])){
	$vm = $_POST["view_mode"];
	if ($vm != "w" && $vm != "c")
		send_response($HTTP_BAD_REQUEST, "Invalid view mode");
	$view_mode = "-".$vm;
}
$script_args = $script_args." ".$view_mode;

// Force depth
if (isset($_POST["force_depth"])){
	if (isset($_POST["forced_depth"]) && ctype_digit($_POST["forced_depth"])){
		$fd = intval($_POST["forced_depth"]);
		if ($fd < 0 || $fd > 100){
			send_response($HTTP_BAD_REQUEST, "Invalid depth value");
		}
		$fd = $fd/100.0;
		$script_args = $script_args." --forcedepth ".$fd;
	}
}

// Execute script

$OUTPUT_DIR = "out";  // Must be relative to this script's location
$script_args = $script_args." -o \"".getcwd()."/".$OUTPUT_DIR."\"";

// send_response(400, "Args so far: ".$script_args);

$sirds_path = "/home/mexomagno/Workspace_ext4/stereogramaxo";

//$cmd_text = "$sirds_path/ENV/bin/python $sirds_path/sirds.py -d $sirds_path/depth_maps/tiburon.png --dots -w --blur 6 --forcedepth 1 -o out";
$cmd_text = $sirds_path."/ENV/bin/python $sirds_path/sirds.py ".$script_args;
$cmd = escapeshellcmd($cmd_text);

# Expect a JSON with results
$script_response = exec($cmd, $cmd_output, $shell_retcode);

$response_data = "";

switch($shell_retcode){
	case 0:
		// Get generated file name
		$json_response = json_decode($script_response);
		$json_response->text = $OUTPUT_DIR."/".$json_response->text;
		send_response($json_response->code, $json_response);
	case 126:
		send_response($HTTP_SERVER_ERROR, "Server has permission issues! Fix first");
	default:
		send_response($HTTP_SERVER_ERROR, "Unknown error happened on the server"); 
}
?>