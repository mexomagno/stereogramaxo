# Stereogramaxo
####*Yet Another Autostereogram Generator*
--------------
This is a weekend project I made out of common boredom and genuine love and curiosity for these [beautiful works of art](https://en.wikipedia.org/wiki/Autostereogram).
Written in python for the sake of simplicity, and relays on the active PIL fork, [**Pillow**](https://python-pillow.github.io/) for image processing.

###Some Results:
<img src="https://raw.githubusercontent.com/mexomagno/stereogramaxo/master/tres_tiburones.png" alt="Sharkies" width="750px;">

###Features:
- Random dot patterns and image-based patterns supported
- Multiple file formats supported for both depth-maps and image patterns
- Wall-eyed and Cross-eyed generation
- Supports random depth-map selection, random pattern selection and both altogether
- Generated stereograms can be saved on many image file formats
- Implements Oversampling for smoother surface depth levels (only for image-based patterns)

###TODO:
- Write a decent --help menu
- Maybe develop a friendlier GUI
- Optimize stereogram generation algorithm

###Coming soon:
If you take a look at the files on the repository, you'll see *"animated_sirds.py"*.
This is a script capable of generating animated videos based on a collection of depthmaps and a preselected pattern.
Currently it's capable of indeed generating a video file with the animation, but it's still very rough to use and error prone. I'll soon upload a demo video.
