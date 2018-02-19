# Stereogramaxo

#### *Yet Another Autostereogram Generator*

--------------

This is a weekend project I made out of common boredom and genuine love and curiosity for these [beautiful works of art](https://en.wikipedia.org/wiki/Autostereogram).
It is written in python for the sake of simplicity, and relays on the active PIL fork, [**Pillow**](https://python-pillow.github.io/) for image processing.

## Examples:

<img src="https://raw.githubusercontent.com/mexomagno/stereogramaxo/master/tres_tiburones.png" alt="Sharkies" width="750px;">


## Usage:
Install the required packages, then run the code with
```
~$: ./sirds.py
```

Choose your options on the GUI and you're done!

<img src="https://raw.githubusercontent.com/mexomagno/stereogramaxo/master/neat_gui.png" alt="Neat GUI">


### Features
- Support for **Random dot** and **image-based** patterns
- Extensive image file formats supported
- Supports [**Wall-eyed** and **Cross-eyed**](https://en.wikipedia.org/wiki/Autostereogram#Simulated_3D_perception) generation
- Simple but neat GUI :)
- Pixel displacement can be set from left to right or from center to sides
- Preset depth maps and patterns included (can be chosen randomly)
- Text depth maps can be generated
- Results can be saved to disk
- Implements Oversampling for smoother surface depth levels (only for image-based patterns)


## Limitations
- Tested on Python 2.7 only.
- On ubuntu, you have to manually install the *python-tk* module via Aptitude to use the GUI


### TODO:
- Speed up generation (multi threading?)
- Translate code
- Solve "leftmost-column" bug
- Offer as a web service for portability
- Hidden-surface removal (removes artifacts) *(this one might never be done...)*

### Coming soon-ish:
If you take a look at the files on the repository, you'll see *"animated_sirds.py"*.
This is a script capable of generating animated videos based on a collection of depthmaps and a preselected pattern.
Currently it's capable of indeed generating a video file with the animation, but it's still very rough to use and error prone. I'll "soon" upload a demo video (I will when I manage to generate depth map animations)

I'm also thinking of generating animated gifs that vary the depth, patterns, and smoothness.