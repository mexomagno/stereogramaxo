# Stereogramaxo
####*Yet Another Autostereogram Generator*
--------------
This is a weekend project I made out of common boredom and genuine love and curiosity for these [beautiful works of art](https://en.wikipedia.org/wiki/Autostereogram).
It is written in python for the sake of simplicity, and relays on the active PIL fork, [**Pillow**](https://python-pillow.github.io/) for image processing.

**Some considerations**: 
- Tested on Python 2.7 only.
- On ubuntu, you have to manually install the *python-tk* module via Aptitude to use the GUI
- It has not been tested with the original PIL library. Beware.

###Usage:
Install the required packages, then run the code with
```
~$: ./sirds.py
```

Choose your options on the GUI and you're done!
<img src="https://raw.githubusercontent.com/mexomagno/stereogramaxo/master/neat_gui.png" alt="Neat GUI">

###Some Results:
<img src="https://raw.githubusercontent.com/mexomagno/stereogramaxo/master/tres_tiburones.png" alt="Sharkies" width="750px;">

###Features:
- Random dot patterns and image-based patterns supported
- Multiple file formats supported for both depth-maps and image patterns
- Wall-eyed and Cross-eyed generation
- Simple but neat GUI :)
- Pixel displacement can be set from left to right or from center to sides
- Supports random depth-map selection, random pattern selection and both altogether
- Generated stereograms can be saved in many image file formats
- Implements Oversampling for smoother surface depth levels (only for image-based patterns)

###TODO:
- Hidden-surface removal (removes artifacts) *(this one might never be done...)*
- Optimize stereogram generation algorithm

###Coming soon:
If you take a look at the files on the repository, you'll see *"animated_sirds.py"*.
This is a script capable of generating animated videos based on a collection of depthmaps and a preselected pattern.
Currently it's capable of indeed generating a video file with the animation, but it's still very rough to use and error prone. I'll "soon" upload a demo video (I will when I manage to generate depth map animations)


