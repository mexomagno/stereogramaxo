#!/usr/bin/python
# coding: utf-8
from __future__ import print_function
import os
from random import choice, random
import json
# This "PIL" refers to Pillow, the PIL fork. Check https://pillow.readthedocs.io/en/3.3.x
from PIL import Image as im, ImageDraw as imd
# GUI
from Tkinter import *
import tkFileDialog
import tkFont

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


class SettingsWindow:
    # CONSTANTS
    DEPTHMAP_RANDOM = 0
    DEPTHMAP_SHARK = 1
    DEPTHMAP_FILE = 2
    DEPTHMAP_TEXT = 3
    PATTERN_DOTS = 0
    PATTERN_RANDOM = 1
    PATTERN_FILE = 2
    MODE_WALLEYED = 0
    MODE_CROSSEYED = 1
    WINDOW_HEIGHT = 600
    WINDOW_WIDTH = 800
    WINDOW_POSITION_X = 100
    WINDOW_POSITION_Y = 30
    COLOR_ERROR = "#ff0000"
    COLOR_CHOSEN_FILE = "#002288"
    FONT_SECTION_TITLE = {"family": "Helvetica", "size": 12, "weight": "bold"}
    FONT_CHOSEN_FILE = {"family": "Helvetica", "size": 10, "weight": "normal"}
    FONT_GENERATE_BUTTON = {"family": "Helvetica", "size": 13, "weight": "bold"}
    FONT_SECTION_SUBTITLE = {"family": "Helvetica", "size": FONT_SECTION_TITLE["size"] - 2, "weight": "bold"}
    # DEFAULTS
    DEFAULT_DEPTHMAP_SELECTION = DEPTHMAP_FILE
    DEFAULT_PATTERN_SELECTION = PATTERN_DOTS
    DEFAULT_MODE_SELECTION = MODE_WALLEYED
    DEFAULT_DONTSAVE_VALUE = True
    DEFAULT_DEPTHMAP_FILE = "depth_maps/tiburon.png"
    SHARK_PATH = "depth_maps/tiburon.png"
    DEFAULT_DEPTH_MULTIPLIER = 1
    DEFAULT_DEPTHMAP_GAUSSIAN_BLUR = 0
    DEFAULT_DEPTHTEXT_DEPTH = 50
    DEFAULT_DEPTHTEXT_FONTSIZE = 130

    DEPTHMAP_OPTIONS = [
        ("Shark", DEPTHMAP_SHARK),
        ("Custom File", DEPTHMAP_FILE),
        ("Text", DEPTHMAP_TEXT),
    ]
    PATTERN_OPTIONS = [
        ("Dots", PATTERN_DOTS),
        ("Random", PATTERN_RANDOM),
        ("Custom pattern", PATTERN_FILE)
    ]

    def __init__(self, parent, current_settings):
        self.window_root = Toplevel(parent)
        self.window_root.geometry("+{}+{}".format(self.WINDOW_POSITION_X, self.WINDOW_POSITION_Y))
        self.window_root.title = "Settings"
        self._persistent_settings = current_settings  # Copy of current settings
        main_frame = Frame(self.window_root)
        main_frame.pack()
        # main elements
        depthmap_frame = Frame(self.window_root)
        depthmap_frame.pack(anchor=NE)
        pattern_frame = Frame(self.window_root)
        pattern_frame.pack(anchor=NE)
        mode_frame = Frame(self.window_root)
        mode_frame.pack()
        saving_settings_frame = Frame(self.window_root)
        saving_settings_frame.pack()
        advanced_settings_frame = Frame(self.window_root)
        advanced_settings_frame.pack()

        generate_button_bg_color = "#555555"
        generate_button_fg_color = "#ffffff"
        # depthmap settings
        self.add_depthmap_settings(depthmap_frame)
        # Pattern settings
        self.add_pattern_settings(pattern_frame)
        # Mode selection
        self.add3dModeSettings(mode_frame)
        # output filename
        self.addSavingSettings(saving_settings_frame)
        # Advanced settings
        self.addAdvancedSettings(advanced_settings_frame)

        # Generate button
        b = Button(self.window_root, text="Generate!", command=self.endWindowProcess, font=self.FONT_GENERATE_BUTTON,
                   bg=generate_button_bg_color, fg=generate_button_fg_color)
        b.pack(side=BOTTOM)

        # self.output_filepath = ""

    # TKinter element generators
    def newSectionTitle(self, root, text):
        return Label(root, text=text, font=self.makeFont(self.FONT_SECTION_TITLE))

    def makeFont(self, font):
        return tkFont.Font(family=font["family"], size=font["size"], weight=font["weight"])

    def add_depthmap_settings(self, root):
        dm_selection = self._persistent_settings.get_depthmap_selection()

        # Title
        self.newSectionTitle(root, "Depthmap selection").pack(anchor=CENTER)

        # Default depthmap selection
        self.tk_depthmap_selection = IntVar()
        if dm_selection == "text":
            self.tk_depthmap_selection.set(self.DEPTHMAP_TEXT)
        else:
            # A file was selected
            if self._persistent_settings.get_depthmap_path() == self.SHARK_PATH:
                self.tk_depthmap_selection.set(self.DEPTHMAP_SHARK)
            else:
                self.tk_depthmap_selection.set(self.DEPTHMAP_FILE)

        # Depthmap options (text, file, etc)
        depthmap_options_frame = Frame(root)
        depthmap_options_frame.pack(anchor=CENTER)
        for i in range(len(self.DEPTHMAP_OPTIONS)):
            text, option = self.DEPTHMAP_OPTIONS[i]
            new_frame = Frame(depthmap_options_frame)
            new_frame.grid(row=0, column=i)
            if option == self.DEPTHMAP_TEXT:
                b = Radiobutton(new_frame, text=text, variable=self.tk_depthmap_selection, value=option,
                                command=self.update_depthmap_selection)
                b.pack(side=TOP, anchor=CENTER)
                self.tk_depthmap_text = Entry(new_frame)
                self.tk_depthmap_text.pack(side=BOTTOM, anchor=CENTER)
                self.tk_depthmap_text.insert(0, self._persistent_settings.get_depthmap_text())
            elif option == self.DEPTHMAP_FILE:
                # Write path from persistent settings
                b = Radiobutton(new_frame, text=text, variable=self.tk_depthmap_selection, value=option,
                                command=self.update_depthmap_selection)
                b.pack(side=LEFT, anchor=N)
                self.tk_depthmap_browse_button = Button(new_frame, text="Browse...", command=self.ask_open_depthmap_file,
                                                        state=DISABLED)
                self.tk_depthmap_browse_button.pack(side=TOP, anchor=N)
                self.tk_last_depthmap_chosen = StringVar()
                self.tk_last_depthmap_chosen.set(
                    self._persistent_settings.get_depthmap_path() if
                    self._persistent_settings.get_depthmap_selection() == "file" else
                    "")
                self._depthmap_file_path = self.tk_last_depthmap_chosen.get()
                print("initialized depthmap path: {}".format(self._depthmap_file_path))
                self.tk_chosen_depthmap_label = Label(new_frame, textvariable=self.tk_last_depthmap_chosen,
                                                      font=self.makeFont(self.FONT_CHOSEN_FILE),
                                                      fg=self.COLOR_CHOSEN_FILE)
                self.tk_chosen_depthmap_label.pack(side=BOTTOM, anchor=S)
            elif option == self.DEPTHMAP_SHARK:
                # Write path from persistent settings
                b = Radiobutton(new_frame, text=text, variable=self.tk_depthmap_selection, value=option,
                                command=self.update_depthmap_selection)
                b.pack(side=LEFT, anchor=N)


        self.update_depthmap_selection()

    def add_pattern_settings(self, root):
        self.newSectionTitle(root, "Pattern selection").pack()
        self.tk_pattern_selection = IntVar()
        # set selection from settings
        last_selection_raw = self._persistent_settings.get_pattern_selection()
        print("last pattern selection: {}".format(last_selection_raw))
        if last_selection_raw == _PersistentSettings.DOT_PATTERN:
            self.tk_pattern_selection.set(self.PATTERN_DOTS)
        elif last_selection_raw == _PersistentSettings.RANDOM:
            self.tk_pattern_selection.set(self.PATTERN_RANDOM)
        else:
            self.tk_pattern_selection.set(self.PATTERN_FILE)
        print("pattern selection: {}".format(self.tk_pattern_selection.get()))
        for text, option in self.PATTERN_OPTIONS:
            b = Radiobutton(root, text=text, variable=self.tk_pattern_selection, value=option,
                            command=self.update_pattern_selection)
            b.pack(anchor=NW, side=LEFT)
        self.tk_pattern_browse_button = Button(root, text="Browse...", command=self.ask_open_pattern_file,
                                               state=DISABLED)
        self.tk_pattern_browse_button.pack(anchor=NW, side=LEFT)
        self.tk_last_pattern_chosen = StringVar()
        self.tk_last_pattern_chosen.set("")
        self.tk_chosen_pattern_label = Label(root, textvariable=self.tk_last_pattern_chosen,
                                             font=self.makeFont(self.FONT_CHOSEN_FILE),
                                             fg=self.COLOR_CHOSEN_FILE)
        self.tk_chosen_pattern_label.pack()
        self.update_pattern_selection()

    def add3dModeSettings(self, root):
        self.newSectionTitle(root, "3D Viewing Mode").pack()
        self.mode_selection = IntVar()
        self.mode_selection.set(SettingsWindow.DEFAULT_MODE_SELECTION)
        b = Radiobutton(root, text="Wall-eyed", variable=self.mode_selection, value=self.MODE_WALLEYED,
                        indicatoron=0)
        b.pack(side=LEFT)
        b.select()
        b2 = Radiobutton(root, text="Cross-eyed", variable=self.mode_selection,
                         value=SettingsWindow.MODE_CROSSEYED, indicatoron=0)
        b2.pack(side=LEFT)

    def addSavingSettings(self, root):
        self.newSectionTitle(root, "Saving").pack()
        self.save_button = Button(root, text="Save as...", command=self.askSaveAs)
        self.save_button.pack(side=LEFT)
        self.last_outputname_chosen = StringVar()
        self.last_outputname_chosen.set("")
        self.chosen_outputname_label = Label(root, textvariable=self.last_outputname_chosen,
                                             font=self.makeFont(self.FONT_CHOSEN_FILE),
                                             fg=self.COLOR_CHOSEN_FILE)
        self.chosen_outputname_label.pack(side=LEFT)
        self.dont_save_variable = BooleanVar()
        self.dont_save_variable.set(self.DEFAULT_DONTSAVE_VALUE)
        self.dont_save_checkbox = Checkbutton(root, text="I don't wanna save it!",
                                              variable=self.dont_save_variable, command=self.updateSaveButton)
        self.dont_save_checkbox.pack(side=RIGHT)
        self.updateSaveButton()

    def addAdvancedSettings(self, root):
        self.newSectionTitle(root, "Advanced Settings").pack()
        # Depthmap smoothness
        depthmap_smoothness_frame = Frame(root)
        depthmap_smoothness_frame.pack(anchor=E)
        Label(depthmap_smoothness_frame, text="Depthmap gaussian blur level",
              font=self.makeFont(self.FONT_SECTION_SUBTITLE)).pack(side=LEFT)
        self.depthmap_smoothness_scale = Scale(depthmap_smoothness_frame, from_=0, to=10, orient=HORIZONTAL,
                                               resolution=0.1)
        self.depthmap_smoothness_scale.pack(side=LEFT)
        self.depthmap_smoothness_scale.set(self.DEFAULT_DEPTHMAP_GAUSSIAN_BLUR)
        # Depth multiplier
        depth_multiplier_frame = Frame(root)
        depth_multiplier_frame.pack(anchor=E)
        Label(depth_multiplier_frame, text="Depth ammount", font=self.makeFont(self.FONT_SECTION_SUBTITLE)).pack(
            side=LEFT)
        self.depth_multiplier_scale = Scale(depth_multiplier_frame, from_=0, to=1, orient=HORIZONTAL, resolution=0.1)
        self.depth_multiplier_scale.pack(side=LEFT)
        self.depth_multiplier_scale.set(self.DEFAULT_DEPTH_MULTIPLIER)
        # Dot colors

    ## Some logic

    def updateSaveButton(self):
        if self.dont_save_variable.get():
            self.save_button["state"] = DISABLED
            self.last_outputname_chosen.set("")
            self.output_filepath = ""
        else:
            self.save_button["state"] = NORMAL

    def askSaveAs(self):
        self.output_filepath = tkFileDialog.asksaveasfilename(filetypes=SUPPORTED_OUTPUT_IMAGE_FORMATS)
        self.chosen_outputname_label.config(fg=SettingsWindow.COLOR_CHOSEN_FILE)
        self.last_outputname_chosen.set("Will save as '{}'".format(os.path.basename(self.output_filepath)))

    def ask_open_file(self, which):
        """
        Show 'browse file' dialog

        Parameters
        ----------
        which : str
            "d" for depthmap. "p" for background pattern

        Returns
        -------
        None
        """
        # Initialdir in desktop by default
        initialdir = os.path.expanduser("~/Desktop")

        # Try to get
        initialfile = self._persistent_settings.get_depthmap_path() if which == "d" else self._persistent_settings.get_pattern_selection()
        print("Currently selected file: {}".format(initialfile))
        if initialfile != "" and os.path.exists(initialfile):
            initialdir = os.path.dirname(initialfile)

        # TODO: Show image thumbnail instead of (or appended to) image name
        Tk().withdraw()
        # Obtain selected filename
        selected_file_path = tkFileDialog.askopenfilename(
            initialdir=initialdir,
            filetypes=(SUPPORTED_INPUT_IMAGE_FORMATS + [("Show all files", "*")]))
        if which == "d":
            # Save selected depthmap file path
            print ("New file selected: {}".format(selected_file_path))
            if selected_file_path != "":
                self.tk_last_depthmap_chosen.set(os.path.basename(selected_file_path))
                self._persistent_settings.select_depthmap("file", selected_file_path)
                self.tk_chosen_depthmap_label.config(fg=SettingsWindow.COLOR_CHOSEN_FILE)
        elif which == "p":
            print ("New pattern file selected: {}".format(selected_file_path))
            if selected_file_path != "":
                self.tk_last_pattern_chosen.set(os.path.basename(selected_file_path))
                self._persistent_settings.select_pattern(selected_file_path)
                self.tk_chosen_pattern_label.config(fg=SettingsWindow.COLOR_CHOSEN_FILE)

    def ask_open_depthmap_file(self):
        self.ask_open_file("d")

    def ask_open_pattern_file(self):
        self.ask_open_file("p")

    def update_depthmap_selection(self):
        """ Edit tkinter elements to show new depthmap selection """
        # Enable / disable text input
        if self.tk_depthmap_selection.get() == self.DEPTHMAP_TEXT:
            self.tk_depthmap_text["state"] = NORMAL
        else:
            self.tk_depthmap_text["state"] = DISABLED
            # Rescue whatever text was entered
            self._persistent_settings.select_depthmap("text", self.tk_depthmap_text.get())
            self._persistent_settings.select_depthmap("file", self._persistent_settings.get_depthmap_path())
        # enable / disable "browse..." button
        if self.tk_depthmap_selection.get() == self.DEPTHMAP_FILE:
            self.tk_last_depthmap_chosen.set(os.path.basename(self._persistent_settings.get_depthmap_path()))
            self.tk_depthmap_browse_button["state"] = NORMAL
        else:
            self.tk_depthmap_browse_button["state"] = DISABLED
            self.tk_last_depthmap_chosen.set("")

        if self.tk_depthmap_selection.get() == self.DEPTHMAP_SHARK:
            self._persistent_settings.select_depthmap("file", self.SHARK_PATH)

    def update_pattern_selection(self):
        # Browse button enabled
        if self.tk_pattern_selection.get() == self.PATTERN_FILE:
            selected_pattern = self._persistent_settings.get_pattern_selection()
            if selected_pattern != _PersistentSettings.RANDOM and selected_pattern != _PersistentSettings.DOT_PATTERN:
                self.tk_last_pattern_chosen.set(os.path.basename())
            self.tk_pattern_browse_button["state"] = NORMAL
        else:
            self.tk_pattern_browse_button["state"] = DISABLED
            self.tk_last_pattern_chosen.set("")
            if self.tk_pattern_selection.get() == self.PATTERN_DOTS:
                self._persistent_settings.select_pattern(_PersistentSettings.DOT_PATTERN)
            elif self.tk_pattern_selection.get() == self.PATTERN_RANDOM:
                self._persistent_settings.select_pattern(_PersistentSettings.RANDOM)

    def endWindowProcess(self):
        # At this point, settings are stored in internal settings variable
        self.window_root.destroy()

    def get_persistent_settings(self):
        return self._persistent_settings


def receive_arguments_from_gui(settings):
    """
    Use Gui interface to ask user for options

    Parameters
    ----------
    settings_dict : _PersistentSettings
        Settings to display

    Returns
    -------
    _PersistentSettings
        Modified settings
    """
    root = Tk()
    root.withdraw()
    w = SettingsWindow(root, settings)
    root.wait_window(w.window_root)
    modified_settings = w.get_persistent_settings()
    root.destroy()
    return modified_settings


def main():
    loaded_settings = _PersistentSettings()
    print(u"Loaded settings: {}".format(loaded_settings.__unicode__()))
    new_settings = receive_arguments_from_gui(loaded_settings)
    print(u"Modified settings: '{}'".format(new_settings.__unicode__()))
    new_settings.dump_to_file()
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
