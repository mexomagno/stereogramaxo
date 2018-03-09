<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<title>Testing</title>
	<link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/foundation/6.4.3/css/foundation.min.css">
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/motion-ui/1.1.1/motion-ui.min.css">
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-colorpicker/2.5.1/css/bootstrap-colorpicker.min.css">
	<style>
	body{
		margin: 0px auto;
		background-color: #eee;
		/*transform: scale(0.9);
   		transform-origin: 0 0;*/
	}
	#debug-div{
		color: #ff0000;
		font-variant: monospace;
	}

	#loading-icon {
		display: none;
		width: 100px;
		height: 100px;
		border-radius: 50px;
		margin-left: auto;
		margin-right: auto;
	}
	.panel-hidden {
		display: none;
	}

	#the-form {
		max-width: 70%;
		margin: 20px auto;
	}
	#title {

	}

	#submit-container{
		margin: 20px auto;
	}
	#submit {
		font-size: 150%;
	}

	.justify-center{
		text-align: center;
	}
	#generated-image{
		width: auto;
		height: auto;
		max-width: 90%;
		max-height: 90%;
	}
	.primary{
		font-size: 110%;
	}
		
	#switch-paddle-label{
		margin-left: auto;
		margin-right: auto;
	}
	.callout{
		margin: -1px;
	}
	.has-tip{
		border-bottom: none;
		cursor: pointer;
	}
	.form-error{
		font-size: 120%;
	}
	</style>
</head>
<body>
	<div class="full reveal justify-center" id="generated-image-modal" data-reveal data-close-on-click="true" data-animation-in="fade-in slow" data-animation-out="fade-out slow" data-v-offset="0">
		<img id="generated-image">
		<button class="close-button" data-close aria-label="Close reveal" type="button">
			<span aria-hidden="true">&times;</span>
		</button>
	</div>
	<form action="#" id="the-form" method="post" data-abide="ajax">
		<div id="title" class="grid-x">
			<h1 class="justify-center cell auto">Stereogramaxo</h2>
		</div>
		<div class="grid-x">
			<h3 class="justify-center cell auto">Control Panel</h3>
		</div>
		<br><br>
		<!-- Depthmap selector -->
		<div class="grid-x justify-center callout small">
			<!-- switches -->
			<div class="cell large-2">
				<div class="has-tip left" data-tooltip title="Grayscale image used to create the 3D illusion. Upload an image or input some text.">Depthmap</div>
				<div class="switch">
				<input class="switch-input" id="dm-file-switch" type="radio" checked value="file" name="dm_switches" onchange="radio_changed(this, 'dm-file-input-panel', ['dm-text-panel']);">
				<label class="switch-paddle" for="dm-file-switch">
					<span class="show-for-sr">Depthmap</span>
					<span class="switch-active" aria-hidden="true">File</span>
				</label>
				</div>
				<div class="switch">
				<input class="switch-input" id="dm-text-switch" type="radio" value="text" name="dm_switches" onchange="radio_changed(this, 'dm-text-panel', ['dm-file-input-panel']);">
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
						<input type="file" id="depthmap-file" name="depthmap_file" class="show-for-sr file-selector" data-validator="valid_depthmap_file">
						<span class="form-error">Select a file first</span>
						<div id="depthmap-filename" class="justify-center" placeholder="Select a depthmap file"></div>
					</div>
					<!-- Text input -->
					<div id="dm-text-panel" class="panel-hidden">
						<label for="depthmap-text"></label>
						<input type="text" id="depthmap-text" name="depthmap_text" value="K paza" maxlength="30" data-validator="valid_depthmap_text">
						<span class="form-error">Enter some text first</span>
						<div id="chars-left"></div>
					</div>
				</div>
			</div>
		</div>
		<!-- Pattern selector -->
		<div class="grid-x justify-center callout small">
			<!-- switches -->
			<div class="cell large-2">
				<div class="has-tip left" data-tooltip title="What to put as a background. Provide an image or select a random dot pattern">Background Pattern</div>
				<div class="switch">
					<input class="switch-input" id="pattern-file-switch" type="radio" value="file" checked name="pattern_switches" onchange="radio_changed(this, 'pattern-file-input-panel', ['pattern-dots-settings-panel']);">
					<label class="switch-paddle" for="pattern-file-switch">
						<span class="show-for-sr">Patterns</span>
						<span class="switch-active" aria-hidden="true">File</span>
					</label>
				</div>
				<div class="switch">
					<input class="switch-input" id="pattern-dots-switch" type="radio" value="dots" name="pattern_switches" onchange="radio_changed(this, 'pattern-dots-settings-panel', ['pattern-file-input-panel']);">
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
					<input type="file" id="pattern-file" name="pattern_file" class="show-for-sr file-selector" data-validator="valid_pattern_file">
					<span class="form-error">Select a file first</span>
					<div id="pattern-filename" class="justify-center" placeholder="Select a pattern file"></div>
				</div>
				<div id="pattern-dots-settings-panel" class="panel-hidden">
					<div class="grid-x">
						<!-- dot probability -->
						<!-- <div class="cell large-12"> -->
							<div class="cell large-6">
								<div>Probability of dot apparition</div>
							</div>
							<div class="cell large-6">
								<div class="grid-x">
									<div class="cell large-10">
										<div class="slider" data-slider data-initial-start="40" data-step="1">
											<span class="slider-handle" data-slider-handle role="slider" tabindex="1" aria-controls="dot-probability-slider"></span>
										</div>
									</div>
									<div class="cell large-2">
										<input type="number" id="dot-probability-slider" name="dot_probability" min="10" max="50">
									</div>
								</div>
							</div>
						<!-- </div> -->
						<!-- background color -->
						<div class="cell large-12">
							<div class="grid-x">
								<div class="cell large-6">
									<div>Background color</div>
								</div>
								<div class="cell large-6">
									<input type="text" class="jscolor" id="bg-color-picker" value="000000" name="dot_bg_color">
									<!-- <span class="form-error">Invalid color</span> -->
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
		<!-- Blur selector -->
		<div class="grid-x justify-center callout small">
			<!-- label -->
			<div class="cell large-2">
				<div class="has-tip left" data-tooltip title="Applies a Gausian Blur filter over the original depthmap. Play with it and see!">Gaussian Blur</div>
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
		<div class="grid-x justify-center callout small">
			<!-- Switch -->
			<div class="cell large-2">
				<div class="has-tip left" data-tooltip title="Force a distance between the farthest and nearest points (Useful in case that your depthmap is too flat)">Force Depth</div>
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
						<input type="number" id="forced-depth-slider" disabled>
						<input type="hidden" name="forced_depth" id="forced-depth">
					</div>
				</div>
			</div>
		</div>
		<!-- View mode -->
		<div class="grid-x justify-center callout small">
			<div class="cell large-2">
				<div class="has-tip left" data-tooltip title="Most common is Wall-eyed. If you feel you're seeing an inverted stereogram, try the other view mode">View Mode</div>
			</div>
			<div class="cell large-10">
				<div class="grid-x">
					<div class="cell large-5 callout" id="wall-eyed-label">Wall-Eyed</div>
					<div class="cell large-2 clearfix">
						<div class="switch large float-center">
							<input class="switch-input" id="view-mode-switch" type="checkbox">
							<input type="hidden" id="view-mode" name="view_mode">
							<label class="switch-paddle" for="view-mode-switch" id="switch-paddle-label">
								<span class="show-for-sr"></span>
							</label>
						</div>
					</div>
					<div class="cell large-5 callout" id="cross-eyed-label">Cross-Eyed</div>
				</div>
			</div>
		</div>

		<!-- Submit -->
		<div class="grid-x">
			<!-- <div class="cell large-2"></div> -->
			<!-- <div class="cell large-12"> -->
				<div class="justify-center" id="submit-container">
					<input id="submit" type="submit" class="button" value="GENERATE">
					<video id="loading-icon" autoplay loop muted>
						<source type="video/webm" src="https://giant.gfycat.com/AppropriateSpotlessAdouri.webm">
					</video>
				</div>
			<!-- </div> -->
		</div>
	</form>

	<pre><div id="debug-div"></div></pre>

	<script src="https://code.jquery.com/jquery-3.3.1.min.js"></script>
	<script src="https://cdnjs.cloudflare.com/ajax/libs/foundation/6.4.3/js/foundation.min.js"></script>
	<script src="https://cdnjs.cloudflare.com/ajax/libs/jscolor/2.0.4/jscolor.min.js"></script>
	<script>


	Foundation.Abide.defaults.validators["valid_depthmap_file"] = 
	function ($el, required, parent){
		if ($("#dm-file-switch").is(":checked") && $el.val() == "")
			return false;
		return true;
	};
	Foundation.Abide.defaults.validators["valid_depthmap_text"] = 
	function ($el, required, parent){
		if ($("#dm-text-switch").is(":checked") && $el.val() == "")
			return false;
		return true;
	}
	Foundation.Abide.defaults.validators["valid_pattern_file"] = 
	function ($el, required, parent){
		if ($("#pattern-file-switch").is(":checked") && $el.val() == "")
			return false;
		return true;
	}

	$(document).foundation();

	function log(message){
		console.log("response: " + message);
		// $("#debug-div").text(message);
	}

	/**
	To be triggered when a radio input is selected. 
	It activates the associated panel id and hides every other element in ids_to_hide
	**/
	function radio_changed(radio_element, associated_panel_id, ids_to_hide){
		if (!$(radio_element).is(":checked"))
			return;
		var ids = ids_to_hide;
		if (ids_to_hide.constructor != Array)
			ids = Array(ids_to_hide);
		// Hide elements
		for (id of ids){
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

		// View mode switch behavior
		$("#view-mode-switch").change(function(){
			if ($(this).is(":checked")){
				// Cross eyed selected
				// $("#wall-eyed-label").removeClass("label primary");
				// $("#cross-eyed-label").addClass("label primary");
				$("#wall-eyed-label").removeClass("primary");
				$("#cross-eyed-label").addClass("primary");
			} else {
				// Wall eyed selected
				// $("#cross-eyed-label").removeClass("label primary");
				// $("#wall-eyed-label").addClass("label primary");
				$("#cross-eyed-label").removeClass("primary");
				$("#wall-eyed-label").addClass("primary");
			}
			$("#view-mode").val(($(this).is(":checked") ? "c" : "w"));
		});
		$("#view-mode-switch").change();

		// Depthmap mode switch: Change depth depending on the mode
		// TODO: Move slider too
		$("#dm-file-switch").change(function(){
			if ($(this).is(":checked")){
				// Selected file depthmap
				if (!$("#force-depth-switch").is(":checked")){
					$("#forced-depth-slider").val(80);
				}
			}
		});
		$("#dm-text-switch").change(function(){
			if ($(this).is(":checked")){
				// Selected file depthmap
				if (!$("#force-depth-switch").is(":checked")){
					$("#forced-depth-slider").val(20);
				}
			}
		});

		// Text ux
		$("#depthmap-text").keyup(function(event){
			$("#chars-left").text("" + ($(this).attr("maxlength") - $(this).val().length));
		});
		$("#depthmap-text").keyup();

		// File selector filename displays
		$(".file-selector").change(function(){
			var div_element;
			if ($(this).attr("id") == "depthmap-file"){
				div_element = $("#depthmap-filename");
			} else if ($(this).attr("id") == "pattern-file"){
				div_element = $("#pattern-filename");
			}
			// Get selected file so far
			file_basename = _path_basename($(this).val());
			if (file_basename == ""){
				div_element.text("-- " + $(div_element).attr("placeholder") + " --");
			} else {
				div_element.text("Selected: '" + file_basename + "'");
			}
		});

		// Form behaviour
		$("#the-form").submit(function(event){
			if ($(".is-invalid-input").length > 0){
				return false;
			}
			$("#forced-depth").val($("#forced-depth-slider").val());
			event.preventDefault();
			// Show loading
			$("#submit").css("display", "none");
			$("#loading-icon").css("display", "block");
			$.ajax({
				url: "run.php",	
				type: "POST",
				processData: false,
				contentType: false,
				async: true,
				data: new FormData($("#the-form")[0]),
				dataType: 'json'
			}).done(function(data){
				log("OK response: " + data);
				$("#loading-icon").css("display", "none");
				$("#submit").css("display", "block");
				var url = data.text;
				$("#generated-image").attr({
					"src": url
				});
				$("#generated-image-modal").foundation("open");
			}).fail(function(data){
				log("FAIL response: " + data);
				$("#loading-icon").css("display", "none");
				$("#submit").css("display", "block");
			});
			return false;
		});
	});

	function _path_basename(complete_path){
		return complete_path.split(/[\\/]/).pop();
	}



	</script>
</body>
</html>