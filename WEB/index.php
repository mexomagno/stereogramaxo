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
	.panel-hidden {
		display: none;
	}

	#the-form {
		max-width: 50%;
		margin: 20px auto;
	}
	#title {

	}

	#submit {
		margin: 20px auto;
		font-size: 150%;
	}

	</style>
</head>
<body>
	<div id="title">
		<h1>Stereogramaxo</h1>
		<h3>Control Panel</h3>
	</div>
	<form action="#"  onsubmit="return run_stereogramaxo();" id="the-form">
		<!-- Depthmap selector -->
		<div class="grid-x">
			<!-- switches -->
			<div class="cell large-2">
				<div class="switch large">
				<input class="switch-input" id="dm-file-switch" type="radio" checked name="dm-switches" onchange="radio_changed(this, 'dm-file-input-panel', ['dm-text-panel']);">
				<label class="switch-paddle" for="dm-file-switch">
					<span class="show-for-sr">Depthmap</span>
					<span class="switch-active" aria-hidden="true">File</span>
				</label>
				</div>
				<div class="switch large">
				<input class="switch-input" id="dm-text-switch" type="radio" name="dm-switches" onchange="radio_changed(this, 'dm-text-panel', ['dm-file-input-panel']);">
				<label class="switch-paddle" for="dm-text-switch">
					<span class="show-for-sr">Depthmap</span>
					<span class="switch-active" aria-hidden="true">Text</span>
				</label>
				</div>
			</div>
			<!-- Panels -->
			<div class="cell large-10">
					<!-- File selector -->
					<div id="dm-file-input-panel">
						<label for="depthmap-file" class="button expanded">Upload depthmap file</label>
						<input type="file" id="depthmap-file" name="depthmap_file" class="show-for-sr">
					</div>
					<!-- Text input -->
					<div id="dm-text-panel" class="panel-hidden">
						<label for="depthmap-text"></label>
						<input type="text" id="depthmap-text" name="depthmap_text" value="K paza">
					</div>
				</div>
			</div>
		</div>
		<!-- Pattern selector -->
		<div class="grid-x">
			<!-- switches -->
			<div class="cell large-2">
				<div class="switch large">
					<input class="switch-input" id="pattern-file-switch" type="radio" checked name="pattern-switches" onchange="radio_changed(this, 'pattern-file-input-panel', ['pattern-dots-settings-panel']);">
					<label class="switch-paddle" for="pattern-file-switch">
						<span class="show-for-sr">Patterns</span>
						<span class="switch-active" aria-hidden="true">File</span>
					</label>
				</div>
				<div class="switch large">
					<input class="switch-input" id="pattern-dots-switch" type="radio" name="pattern-switches" onchange="radio_changed(this, 'pattern-dots-settings-panel', ['pattern-file-input-panel']);">
					<label class="switch-paddle" for="pattern-dots-switch">
						<span class="show-for-sr">Patterns</span>
						<span class="switch-active" aria-hidden="true">Dots</span>
					</label>
				</div>
			</div>
			<!-- Panels -->
			<div class="cell large-10">
				<div id="pattern-file-input-panel">
					<label for="pattern-file" class="button expanded">Upload pattern file</label>
					<input type="file" id="pattern-file" name="pattern_file" class="show-for-sr">
				</div>
				<div id="pattern-dots-settings-panel" class="panel-hidden">
					<label for="dots-probability-slider">Probability of dot aparition</label>
					<div class="grid-x">
						<div class="cell large-10">
							<div class="slider" data-slider data-initial-start=40 data-step="1">
								<span class="slider-handle" data-slider-handle role="slider" tabindex="1" aria-controls="dot-probability-slider"></span>
							</div>
						</div>
						<div class="cell large-2">
							<input type="number" id="dot-probability-slider" name="dot_probability">
						</div>
					</div>
				</div>
			</div>
		</div>
		<!-- Blur selector -->
		<div class="grid-x">
			<!-- label -->
			<div class="cell large-2">
				<label for="blur-slider">Gaussian Blur</label>
			</div>
			<!-- slider -->
			<div class="cell large-10">
				<div class="grid-x">
					<div class="cell large-10">
						<div class="slider" data-slider data-initial-start="2" data-step="1" data-position-value-function="pow" data-non-linear-base="5">
							<span class="slider-handle" data-slider-handle role="slider" tabindex="1" aria-controls="blur-slider"></span>
						</div>
					</div>
					<div class="cell large-2">
						<input type="number" id="blur-slider" name="blur">
					</div>
				</div>
			</div>
		</div>
		
		<!-- Force depth selector -->
		<div class="grid-x">
			<!-- Switch -->
			<div class="cell large-2">
				<label for="force-depth-switch">Force Depth</label>
				<div class="switch large">
					<input class="switch-input" id="force-depth-switch" type="checkbox" name="force_depth">
					<label class="switch-paddle" for="force-depth-switch">
						<span class="show-for-sr">Enable Forced Depth</span>
					</label>
				</div>
			</div>
			<!-- slider -->
			<div class="cell large-10">
				<div class="grid-x">
					<div class="cell large-10">
						<div class="slider" data-slider data-initial-start="80" data-step="1" id="forced-depth-slider-container">
							<span class="slider-handle" data-slider-handle role="slider" tabindex="1" aria-controls="forced-depth-slider"></span>
						</div>
					</div>
					<div class="cell large-2">
						<input type="number" id="forced-depth-slider" name="forced-depth" disabled>
					</div>
				</div>
			</div>
				
			</div>
		</div>

		<!-- Submit -->
		<div class="grid-x">
				<input id="submit" type="submit" class="button" value="GENERATE">
		</div>
	</form>
		


<!--



	
	<div id="response"></div>
	<img id="generated-image">
	<video id="loading-icon" autoplay loop muted poster="loading.webm">
		<source type="video/webm" src="https://giant.gfycat.com/AppropriateSpotlessAdouri.webm">
	</video>
	
 -->


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

	/**
	To be triggered when a radio input is selected. 
	It activates the associated panel id and hides every other element in ids_to_hide
	**/
	function radio_changed(radio_element, associated_panel_id, ids_to_hide){
		console.log("radio element:" + radio_element + ", panel: " + associated_panel_id + ", ids to hide: " + ids_to_hide);
		if (!$(radio_element).is(":checked"))
			return;
		var ids = ids_to_hide;
		if (ids_to_hide.constructor != Array)
			ids = Array(ids_to_hide);
		// Hide elements
		for (id of ids){
			console.log("Will hide " + id);
			$("#" + id).css("display", "none");
		}
		// Show this radio's panel
		$("#" + associated_panel_id).css("display", "block");
	}

	$(document).ready(function(){
		// Forced depth switch behavior
		$("#force-depth-switch").change(function(){
			if ($(this).is(":checked")){
				// Enable slider
				$("#forced-depth-slider-container").removeClass("disabled");
				$("#forced-depth-slider").removeAttr("disabled");
			} else {
				$("#forced-depth-slider-container").addClass("disabled");
				$("#forced-depth-slider").attr("disabled", "disabled");
			}
		});
		$("#force-depth-switch").change();
	});

	</script>
</body>
</html>