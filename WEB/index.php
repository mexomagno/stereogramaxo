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

	</style>
</head>
<body>
	Tamo probando qlo 
	<form action="#"  onsubmit="return run_stereogramaxo();">
		<input type="submit" class="button" value="Test!!">
	</form>
	<div id="response"></div>


	<script src="https://code.jquery.com/jquery-3.3.1.min.js"></script>
	<script src="https://cdnjs.cloudflare.com/ajax/libs/foundation/6.4.3/js/foundation.min.js"></script>
	<script>
	$(document).foundation();
	function run_stereogramaxo(){
		$.ajax({
			url: "run.php",	
		}).done(function(data){
			$("#response").text("response: " + data);
		}).fail(function(data){
			$("#response").text("Error response: " + data);
		});
		return false;
	}
	</script>
</body>
</html>