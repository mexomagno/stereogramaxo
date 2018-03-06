<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<title>Testing</title>
	<link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/foundation/6.4.3/css/foundation.min.css">

	<style>

	#response{
		color: #ff0000;
	}

	#loading-icon {
		display: none;
		width: 100px;
		height: 100px;
		border-radius: 50px;
	}
	</style>
</head>
<body>
	Tamo probando qlo 
	<form action="#"  onsubmit="return run_stereogramaxo();">
		<input type="submit" class="button" value="Test!!">
	</form>
	<div id="response"></div>
	<img id="generated-image">
	<video id="loading-icon" autoplay loop muted poster="loading.webm">
		<source type="video/webm" src="https://giant.gfycat.com/AppropriateSpotlessAdouri.webm">
	</video>
	<script src="https://code.jquery.com/jquery-3.3.1.min.js"></script>
	<script src="https://cdnjs.cloudflare.com/ajax/libs/foundation/6.4.3/js/foundation.min.js"></script>
	<script>
	$(document).foundation();
	function run_stereogramaxo(){
		// Show loading
		$("#loading-icon").css("display", "block");
		$.ajax({
			url: "run.php",	
			type: "POST",
			async: false,
			dataType: 'json'
		}).done(function(data){
			$("#loading-icon").css("display", "none");
			var url = data.text;
			$("#generated-image").attr({
				"src": url
			});
		}).fail(function(data){
			$("#loading-icon").css("display", "none");
			console.log("Response: " + data);
			$("#response").text("Error response: " + data.error);
		});
		return false;
	}

	</script>
</body>
</html>