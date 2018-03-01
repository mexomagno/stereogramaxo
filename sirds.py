#!/usr/bin/python
# coding: utf-8
from __future__ import print_function
import os
from random import choice, random
import json
# This "PIL" refers to Pillow, the PIL fork. Check https://pillow.readthedocs.io/en/3.3.x
from PIL import Image as im, ImageDraw as imd

# Program info
PROGRAM_VERSION = "2.0"

# Default Values
SUPPORTED_INPUT_IMAGE_FORMATS = [
    ("PNG", "*.png"),
    ('JPEG', "*.jpeg"),
    ("Bitmap", "*.bmp"),
    ("EPS", "*.eps"),
    ("GIF", "*.gif"),
    ("JPG", "*.jpg"),
    ("IM", "*.im"),
    ("MSP", "*.msp"),
    ("PCX", "*.pcx"),
    ("PPM", "*.ppm"),
    ("Spider", "*.spider"),
    ("TIFF", "*.tiff"),
    ("WEBP", "*.webp"),
    ("XBM", "*.xbm")
]
DEFAULT_OUTPUT_FILE_FORMAT = "png"
DEFAULT_DEPTHTEXT_FONT = "freefont/FreeSansBold"

# CONSTANTS
SUPPORTED_OUTPUT_IMAGE_FORMATS = SUPPORTED_INPUT_IMAGE_FORMATS
DMFOLDER = "depth_maps"
PATTERNFOLDER = "patterns"
SAVEFOLDER = "saved"

# SETTINGS
SIZE = (800, 600)
PATTERN_FRACTION = 8.0
OVERSAMPLE = 1.8
SHIFT_RATIO = 0.3
LEFT_TO_RIGHT = False  # Defines how the pixels will be shifted (left to right or center to sides
DOT_DRAW_PROBABILITY = 0.4  # Decides how often a random dot is drawn
SMOOTH_DEPTHMAP = True
SMOOTH_FACTOR = 1.8
DOT_OVER_PATTERN_PROBABILITY = 0.3  # Defines how often dots are chosen over pattern on random pattern selection


class _PersistentSettings:
    # Depthmap modes
    DEPTHMAP_TEXT = "depthmap_text"
    DEPTHMAP_FILE = "depthmap_file"

    _DEPTHMAP_FILE = "depthmap_file"
    _DEPTHMAP_TEXT = "depthmap_text"
    _PATTERN = "pattern"
    _EYE_MODE = "eye_mode"
    _OUTPUT_FILE = "output_file"
    DOT_PATTERN = "D"
    RANDOM = "R"

    _SETTINGS_CONTRACT = {
        _DEPTHMAP_FILE: {
            "type": str,
            "default": {
                "value": "depth_maps/tiburon.png",  # path if file, string if text
                "selected": True
            },
        },
        _DEPTHMAP_TEXT: {
            "type": str,
            "default": {
                "value": "Hello World",
                "selected": False
            }
        },
        _PATTERN: {
            "type": str,
            "default": DOT_PATTERN  # "R" == random depthmap, "D" == dots. Else, a path must be inputted
        },
        _EYE_MODE: {
            "type": bool,  # Wall-eyed (True) or cross-eyed (False)
            "default": True,
        },
        _OUTPUT_FILE: {
            "type": str,
            "default": ""
        }
    }

    _DEFAULT_FILE_PATH = ".opts.json"

    def __init__(self):
        # Load everything from file to dict
        self._settings_dict = self._read_or_construct()

    def __unicode__(self):
        return u"{}".format(json.dumps(self._settings_dict, indent=4, sort_keys=True))

    def dump_to_file(self):
        """ Save to a file """
        self._save_to_file(self._settings_dict)

    # DEPTHMAPH
    def get_depthmap_text(self):
        return self._settings_dict[self._DEPTHMAP_TEXT]["value"]

    def get_depthmap_path(self):
        return self._settings_dict[self._DEPTHMAP_FILE]["value"]

    def get_depthmap_selection(self):
        if self._settings_dict[self._DEPTHMAP_TEXT]["selected"]:
            return "text"
        if self._settings_dict[self._DEPTHMAP_FILE]["selected"]:
            return "file"

    def select_depthmap(self, kind, value):
        if kind == "text":
            self._settings_dict[self._DEPTHMAP_TEXT]["value"] = value
            self._settings_dict[self._DEPTHMAP_TEXT]["selected"] = True
            self._settings_dict[self._DEPTHMAP_FILE]["selected"] = False
        else:
            self._settings_dict[self._DEPTHMAP_FILE]["value"] = value
            self._settings_dict[self._DEPTHMAP_FILE]["selected"] = True
            self._settings_dict[self._DEPTHMAP_TEXT]["selected"] = False

    # PATTERN
    def get_pattern_selection(self):
        pattern = self._settings_dict[self._PATTERN]
        if pattern != self.DOT_PATTERN and pattern != self.RANDOM and not os.path.exists(pattern):
            raise ValueError("Pattern file doesn't exist")
        return pattern

    def select_pattern(self, pattern):
        if pattern != self.DOT_PATTERN and pattern != self.RANDOM and not os.path.exists(pattern):
            raise ValueError("Pattern file doesn't exist")
        self._settings_dict[self._PATTERN] = pattern

    @classmethod
    def _is_dict_valid(cls, in_dict):
        return set(cls._SETTINGS_CONTRACT.keys()) == set(in_dict.keys())

    @classmethod
    def _read_from_file(cls, file_path):
        if file_path is None or not os.path.exists(file_path):
            raise ValueError("File doesn't exist!")
        with open(file_path, "r") as settings_file:
            try:
                read_dict = json.load(settings_file)
            except ValueError:
                raise ValueError("Not a valid JSON-structured file")
            if not cls._is_dict_valid(read_dict):
                raise ValueError("Invalid settings")
            print("Correctly read settings from '{}'".format(file_path))
            return read_dict

    @classmethod
    def _read_or_construct(cls):
        if not os.path.exists(cls._DEFAULT_FILE_PATH):
            # Settings file does not exist. Create one with defaults
            cls._generate_presets_file()
        # Now by all means settings file exists. Load
        return cls._read_from_file(cls._DEFAULT_FILE_PATH)

    @classmethod
    def _generate_presets_file(cls):
        new_settings_dict = dict()
        for key in cls._SETTINGS_CONTRACT:
            new_settings_dict[key] = cls._SETTINGS_CONTRACT[key]["default"]
        cls._save_to_file(new_settings_dict)

    @classmethod
    def _save_to_file(cls, settings_dict, file_path=None):
        """
        Saves a settings dict to a file

        Parameters
        ----------
        settings_dict : dict
            The settings dict. Must be valid
        file_path : str
            Path where settings will be stored

        Returns
        -------
        None
        """
        if file_path is None:
            file_path = cls._DEFAULT_FILE_PATH
        # Validate settings dict
        if not cls._is_dict_valid(settings_dict):
            raise ValueError("Invalid settings dict")
        # Store
        with open(file_path, "w") as save_file:
            json.dump(settings_dict, save_file, indent=4, sort_keys=True)
        print("Saved settings to '{}'".format(file_path))


def show_img(i):
    i.show(command="eog")


def make_background(size=SIZE, filename=""):
    pattern_width = (int)(size[0] / PATTERN_FRACTION)
    # Pattern is a little bit longer than original picture, so everything fits on 3D (eye crossing shrinks the picture horizontally!)
    i = im.new("RGB", (size[0] + pattern_width, size[1]), color="black")
    i_pix = i.load()
    if filename == "R" and random() < DOT_OVER_PATTERN_PROBABILITY:
        filename = "dots"
    # Load from picture
    is_image = False
    if filename != "" and filename != "dots":
        pattern = load_file((get_random("pattern") if filename == "R" else filename))
        if pattern is None:
            print("Error al cargar '{}'. Generando con puntos aleatorios.".format(filename))
            filename = ""
        else:
            is_image = True
            pattern = pattern.resize((pattern_width, (int)((pattern_width * 1.0 / pattern.size[0]) * pattern.size[1])),
                                     im.LANCZOS)
            # Repeat vertically
            region = pattern.crop((0, 0, pattern.size[0], pattern.size[1]))
            y = 0
            while y < i.size[1]:
                i.paste(region, (0, y, pattern.size[0], y + pattern.size[1]))
                y += pattern.size[1]
    # Random fill
    if filename == "" or filename == "dots":
        for f in range(i.size[1]):
            for c in range(pattern_width):
                if random() < DOT_DRAW_PROBABILITY:  # choice([True,False,False,False]):
                    i_pix[c, f] = choice([(255, 0, 0), (255, 255, 0), (200, 0, 255)])
    # Repeat fill
    # x = 0
    # rect = (0,0,pattern_width,i.size[1])
    # region = i.crop(rect)
    # while x < i.size[0]:
    # 	i.paste(region,(x,0,x+pattern_iwdth,i.size[1]))
    # 	x += pattern_width
    return i, is_image


def get_random(whatfile="depthmap"):
    """
    Returns a random file from either depthmap folder or patterns folder

    Parameters
    ----------
    whatfile : str
        specifies which folder

    Returns
    -------
    str :
        Randomly chosen absolute file dir

    """
    folder = (DMFOLDER if whatfile == "depthmap" else PATTERNFOLDER)
    return folder + "/" + choice(os.listdir(folder))


def make_stereogram(options, patt="", mode="we"):
    """
    Actually generates the stereogram.

    Parameters
    ----------
    options : dict
        User-issued options
    patt : str
        pattern filename or "dots"
    mode : str
        Wall-eyed or cross-eyed

    Returns
    -------
    PIL.Image.Image :
        Generated stereogram image
    """
    # Load options
    patt = "" if "pattern" not in options else options["pattern"]
    mode = "we" if "cross-eyed" not in options else ("ce" if options["cross-eyed"] else "we")
    # Load stereogram depthmap
    if options["depthmap"] == "text":
        dm = make_depth_text(options["text"]["value"], options["text"]["depth"], options["text"]["fontsize"],
                             DEFAULT_DEPTHTEXT_FONT)
    else:
        dm = load_file((get_random("depthmap") if options["depthmap"] == "R" else options["depthmap"]), 'L')
    if (dm == None):
        print("Aborting")
        exit(1)
    # Apply gaussian blur filter
    if SMOOTH_DEPTHMAP:
        from PIL import ImageFilter as imf
        dm = dm.filter(imf.GaussianBlur(SMOOTH_FACTOR))

    # Create base pattern
    background, isimg = make_background(dm.size, patt)
    # Oversample on image-pattern based background (NOT dots, bad results!)
    if isimg:
        dm = dm.resize(((int)(dm.size[0] * OVERSAMPLE), (int)(dm.size[1] * OVERSAMPLE)))
        background = background.resize(((int)(background.size[0] * OVERSAMPLE), (int)(background.size[1] * OVERSAMPLE)))
    size = dm.size
    pattern_width = (int)(size[0] * 1.0 / PATTERN_FRACTION)
    pt_pix = background.load()
    dm_pix = dm.load()
    # Empirically obtained. In some place they went from 120px on the shallowest point to 90px (25%)
    ponderador = pattern_width * SHIFT_RATIO
    # Shift pixels from center to left
    if not LEFT_TO_RIGHT:
        x_medios_bg = background.size[0] / 2
        rect = (0, 0, pattern_width, background.size[1])
        background.paste(background.crop(rect), (x_medios_bg - pattern_width, 0, x_medios_bg, background.size[1]))
    for f in range(size[1]):
        if LEFT_TO_RIGHT:
            for c in range(pattern_width, background.size[0]):
                # From left to right
                shift = (dm_pix[(c - pattern_width), f] if mode == "we" else (
                255 - dm_pix[(c - pattern_width), f])) / 255.0 * ponderador
                pt_pix[c, f] = pt_pix[c - pattern_width + shift, f]
        else:
            for c in range(x_medios_bg, background.size[0]):
                # Center to right
                shift = (dm_pix[(c - pattern_width), f] if mode == "we" else (
                255 - dm_pix[(c - pattern_width), f])) / 255.0 * ponderador
                pt_pix[c, f] = pt_pix[c - pattern_width + shift, f]
            for c in range(x_medios_bg - 1, pattern_width - 1, -1):
                # Center to left
                shift = (dm_pix[c, f] if mode == "we" else (255 - dm_pix[c, f])) / 255.0 * ponderador
                pt_pix[c, f] = pt_pix[c + pattern_width - shift, f]
    if not LEFT_TO_RIGHT:
        background.paste(background.crop((pattern_width, 0, 2 * pattern_width, background.size[1])), rect)
    if isimg:  # Return from oversampled image
        background = background.resize(((int)(background.size[0] / OVERSAMPLE), (int)(background.size[1] / OVERSAMPLE)),
                                       im.LANCZOS)  # NEAREST, BILINEAR, BICUBIC, LANCZOS
    return background


def make_depth_text(text, depth=50, fontsize=50, font=DEFAULT_DEPTHTEXT_FONT):
    """
    Makes a text depthmap

    Parameters
    ----------
    text : str
        Text to generate
    depth : int
        Desired depth
    fontsize : int
        Size of text
    font : str
        Further font specification

    Returns
    -------
    PIL.Image.Image
        Generated depthmap image
    """
    import PIL.ImageFont as imf
    if depth < 0: depth = 0
    if depth > 100: depth = 100
    fontroot = "/usr/share/fonts/truetype"
    fontdir = "{}/{}.ttf".format(fontroot, font)
    # Create image (grayscale)
    i = im.new('L', SIZE, "black")
    # Draw text with appropriate gray level
    fnt = imf.truetype(fontdir, fontsize)
    imd.Draw(i).text(
        ((SIZE[0] / 2 - fnt.getsize(text)[0] / 2,
          SIZE[1] / 2 - fnt.getsize(text)[1] / 2)),
        text, font=fnt,
        fill=((int)(255.0 * depth / 100)))
    return i


def save_to_file(img, name, fmt=""):
    valid_ext = []
    for ext in SUPPORTED_OUTPUT_IMAGE_FORMATS:
        valid_ext.append(ext[1].split(".")[1].lower())
    print(valid_ext)
    # Three ways to specify a format:
    #   1: Within filename
    #   2: With "format" parameter
    #   3: Default file format
    # Priority is: 1, then 2, then 3
    # Trying to save with image name format
    filename, fileformat = os.path.splitext(os.path.basename(name))
    fileformat = fileformat.replace(".", "")
    dirname = os.path.dirname(name)
    if dirname == "":
        savefolder = SAVEFOLDER
    else:
        savefolder = dirname
    # Try to create folder, if it doesn't exist already
    if not os.path.exists(savefolder):
        try:
            os.mkdir(savefolder)
        except IOError, msg:
            print("Cannot create file: {}".format(msg))
            exit(1)
    if fileformat not in valid_ext:
        # Try with format parameter
        fileformat = fmt
        if fileformat not in valid_ext:
            # Use image extension
            fileformat = img.format
            if fileformat not in valid_ext:
                fileformat = valid_ext[0]
    try:
        finalname = filename + "." + fileformat
        # Check file existence
        i = 1
        while os.path.exists(savefolder + "/" + finalname):
            if i == 1:
                print("WARNING: File '{}' already exists in '{}'".format(finalname, savefolder))
            finalname = "{} ({}).{}".format(filename, i, fileformat)
            i += 1
        r = img.save(savefolder + "/" + finalname)
        print("Saved file as '{}/{}'".format(savefolder, finalname))
        return finalname
    except IOError, msg:
        print("Error trying to save image as '{}/{}': {}".format(savefolder, filename, msg))
        return None


def load_file(name, type=''):
    try:
        i = im.open(name)
        if type != "":
            i = i.convert(type)
    except IOError, msg:
        print("Picture couln't be loaded '{}': {}".format(name, msg))
        return None
    return i


def main():
    loaded_settings = _PersistentSettings()
    print(u"Loaded settings: {}".format(loaded_settings.__unicode__()))
    return

    print("Generating...")
    i = make_stereogram(new_settings_dict)
    print("Displaying...")
    show_img(i)
    if new_settings_dict["output"] != "":
        print("Saving...")
        output = save_to_file(i, new_settings_dict["output"])
        if output is None:
            print("Oops! Couldn't save file!!")


if __name__ == "__main__":
    main()

"""
Problems:
When image sharply changes from one depth to a different one, a part of the surface edge repeats to the right and left.
Internet's explanation is that there are some points one eye shouldn't be able to see, but we nonetheless consider them
in the stereogram. They say it can be fixed... but how?
This is called Hidden Surface Removal.
"""

# TODO: Uncouple strings and common definitions, remove hardcoded messages, dict keys... that sort of stuff
# TODO: Expand grayscale between the two extremes (enhances near-flat depth maps)
# TODO: Try to enlarge grayscale depth
# TODO: Fix Cross-eyed bug
# TODO: Try to fix broken fin on shark
