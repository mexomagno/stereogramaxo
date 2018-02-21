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


class _StereogramSettings:
    """ Persistent settings manager, based on a local json file """
    DEFAULT_FILE_NAME = "./.opts.json"
    SETTINGS_CONTRACT = {
        "eye_mode": {
                        "type": bool,  # Wall-eyed (True) or cross-eyed (False)
                        "default": True
        }
    }

    @classmethod
    def get(cls, file_path=None):
        # Check if file exists
        if file_path is None:
            file_path = cls.DEFAULT_FILE_NAME
        if not os.path.exists(file_path):
            print("Settings file doesn't exist. Will use defaults")
            print("Generating settings file...")
            cls._generate_presets_file()
        # Read from file and return
        return cls._read_from_file(file_path)

    @classmethod
    def dump(cls, in_dict):
        cls._save_to_file(in_dict)

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
            file_path = cls.DEFAULT_FILE_NAME
        # Validate settings dict
        if not cls._is_dict_valid(settings_dict):
            raise ValueError("Invalid settings dict")
        # Store
        with open(file_path, "w") as save_file:
            json.dump(settings_dict, save_file)
        print("Saved settings to '{}'".format(file_path))


    @classmethod
    def _is_dict_valid(cls, in_dict):
        return set(cls.SETTINGS_CONTRACT.keys()) == set(in_dict.keys())

    @classmethod
    def _generate_presets_file(cls):
        new_settings_dict = dict()
        for key in cls.SETTINGS_CONTRACT:
            new_settings_dict[key] = cls.SETTINGS_CONTRACT[key]["default"]
        cls._save_to_file(new_settings_dict)



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


user_settings = dict()


class SettingsWindow:
    # CONSTANTS
    DEPTHMAP_RANDOM = 0
    DEPTHMAP_SHARK = 1
    DEPTHMAP_FILE = 2
    DEPTHMAP_TEXT = 3
    PATTERN_RANDOM = 0
    PATTERN_DOTS = 1
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
    DEFAULT_DEPTHMAP_SELECTION = DEPTHMAP_SHARK
    DEFAULT_PATTERN_SELECTION = PATTERN_DOTS
    DEFAULT_MODE_SELECTION = MODE_WALLEYED
    DEFAULT_DONTSAVE_VALUE = True
    DEFAULT_DEPTHMAP_FILE = "depth_maps/tiburon.png"
    DEFAULT_DEPTH_MULTIPLIER = 1
    DEFAULT_DEPTHMAP_GAUSSIAN_BLUR = 0
    DEFAULT_DEPTHTEXT_DEPTH = 50
    DEFAULT_DEPTHTEXT_FONTSIZE = 130

    DEPTHMAP_OPTIONS = [
        ("Shark", DEPTHMAP_SHARK),
        ("Text", DEPTHMAP_TEXT),
        ("Custom File", DEPTHMAP_FILE)
    ]
    PATTERN_OPTIONS = [
        ("Dots", PATTERN_DOTS),
        ("Random", PATTERN_RANDOM),
        ("Custom pattern", PATTERN_FILE)
    ]

    def __init__(self, parent):
        self.window_root = Toplevel(parent)
        self.window_root.geometry("+{}+{}".format(self.WINDOW_POSITION_X, self.WINDOW_POSITION_Y))
        self.window_root.title = "Settings"
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
        self.addDepthmapSettings(depthmap_frame)
        # Pattern settings
        self.addPatternSettings(pattern_frame)
        # Mode selection
        self.add3dModeSettings(mode_frame)
        # output filename
        self.addSavingSettings(saving_settings_frame)
        # Advanced settings
        self.addAdvancedSettings(advanced_settings_frame)

        # Generate button
        b = Button(self.window_root, text="Generate!", command=self.setUserSettings, font=self.FONT_GENERATE_BUTTON,
                   bg=generate_button_bg_color, fg=generate_button_fg_color)
        b.pack(side=BOTTOM)

        self.depthmap_file_path = ""
        self.pattern_file_path = ""
        self.output_filepath = ""

    # TKinter element generators
    def newSectionTitle(self, root, text):
        return Label(root, text=text, font=self.makeFont(self.FONT_SECTION_TITLE))

    def makeFont(self, font):
        return tkFont.Font(family=font["family"], size=font["size"], weight=font["weight"])

    def addDepthmapSettings(self, root):
        self.newSectionTitle(root, "Depthmap selection").pack()
        self.depthmap_selection = IntVar()
        self.depthmap_selection.set(self.DEFAULT_DEPTHMAP_SELECTION)
        for text, option in self.DEPTHMAP_OPTIONS:
            if option == self.DEPTHMAP_TEXT:
                text_frame = Frame(root)
                text_frame.pack(side=LEFT, anchor=NE)
                b = Radiobutton(text_frame, text=text, variable=self.depthmap_selection, value=option,
                                command=self.updateDepthmapSelection)
                b.pack(side=TOP, anchor=W)
                self.depthmap_text = Entry(text_frame)
                self.depthmap_text.pack(side=BOTTOM, anchor=W)
            else:
                b = Radiobutton(root, text=text, variable=self.depthmap_selection, value=option,
                                command=self.updateDepthmapSelection)
                b.pack(side=LEFT, anchor=NE)

        self.depthmap_browse_button = Button(root, text="Browse...", command=self.askOpenDepthmapFile,
                                             state=DISABLED)
        self.depthmap_browse_button.pack(side=LEFT)
        self.last_depthmap_chosen = StringVar()
        self.last_depthmap_chosen.set("")
        self.chosen_depthmap_label = Label(root, textvariable=self.last_depthmap_chosen,
                                           font=self.makeFont(self.FONT_CHOSEN_FILE),
                                           fg=self.COLOR_CHOSEN_FILE)
        self.chosen_depthmap_label.pack()
        self.updateDepthmapSelection()

    def addPatternSettings(self, root):
        self.newSectionTitle(root, "Pattern selection").pack()
        self.pattern_selection = IntVar()
        self.pattern_selection.set(self.DEFAULT_PATTERN_SELECTION)
        for text, option in self.PATTERN_OPTIONS:
            b = Radiobutton(root, text=text, variable=self.pattern_selection, value=option,
                            command=self.updatePatternSelection)
            b.pack(anchor=NW, side=LEFT)
        self.pattern_browse_button = Button(root, text="Browse...", command=self.askOpenPatternFile,
                                            state=DISABLED)
        self.pattern_browse_button.pack(anchor=NW, side=LEFT)
        self.last_pattern_chosen = StringVar()
        self.last_pattern_chosen.set("")
        self.chosen_pattern_label = Label(root, textvariable=self.last_pattern_chosen,
                                          font=self.makeFont(self.FONT_CHOSEN_FILE),
                                          fg=self.COLOR_CHOSEN_FILE)
        self.chosen_pattern_label.pack()
        self.updatePatternSelection()

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

    def askopenfile(self, which):
        # TODO: Show image thumbnail instead of (or appended to) image name
        Tk().withdraw()
        self.filename = tkFileDialog.askopenfilename(initialdir=os.path.expanduser("~/Desktop"), filetypes=(
        SUPPORTED_INPUT_IMAGE_FORMATS + [("Show all files", "*")]))
        if which == "d":
            self.depthmap_file_path = self.filename
            if self.filename:
                self.chosen_depthmap_label.config(fg=SettingsWindow.COLOR_CHOSEN_FILE)
                self.last_depthmap_chosen.set(os.path.basename(self.filename))
            else:
                self.last_depthmap_chosen.set("")
        elif which == "p":
            self.pattern_file_path = self.filename
            if self.filename:
                self.chosen_pattern_label.config(fg=SettingsWindow.COLOR_CHOSEN_FILE)
                self.last_pattern_chosen.set(os.path.basename(self.filename))
            else:
                self.last_pattern_chosen.set("")

    def askOpenDepthmapFile(self):
        self.askopenfile("d")

    def askOpenPatternFile(self):
        self.askopenfile("p")

    def updateDepthmapSelection(self):
        # Text input enabled
        if self.depthmap_selection.get() == self.DEPTHMAP_TEXT:
            self.depthmap_text["state"] = NORMAL
        else:
            self.depthmap_text["state"] = DISABLED
        # Browse button enabled
        if self.depthmap_selection.get() == self.DEPTHMAP_FILE:
            self.depthmap_browse_button["state"] = NORMAL
        else:
            self.depthmap_browse_button["state"] = DISABLED
            self.last_depthmap_chosen.set("")
            self.depthmap_file_path = ""

    def updatePatternSelection(self):
        # Browse button enabled
        if self.pattern_selection.get() == self.PATTERN_FILE:
            self.pattern_browse_button["state"] = NORMAL
        else:
            self.pattern_browse_button["state"] = DISABLED
            self.last_pattern_chosen.set("")
            self.pattern_file_path = ""

    def setUserSettings(self):
        global user_settings
        # Get settings and update user_settings
        user_settings = {}
        # depthmap
        dm_selection = self.depthmap_selection.get()
        dm_file_path = self.depthmap_file_path
        if dm_selection == SettingsWindow.DEPTHMAP_FILE:
            if not dm_file_path:
                self.chosen_depthmap_label.config(fg=SettingsWindow.COLOR_ERROR)
                self.last_depthmap_chosen.set("First select a file, please :)")
                return
            else:
                user_settings["depthmap"] = dm_file_path
        elif dm_selection == SettingsWindow.DEPTHMAP_SHARK:
            user_settings["depthmap"] = SettingsWindow.DEFAULT_DEPTHMAP_FILE
        elif dm_selection == SettingsWindow.DEPTHMAP_RANDOM:
            user_settings["depthmap"] = "R"
        elif dm_selection == self.DEPTHMAP_TEXT:
            user_settings["depthmap"] = "text"
            user_settings["text"] = {"value": self.depthmap_text.get(),
                                     "fontsize": self.DEFAULT_DEPTHTEXT_FONTSIZE,
                                     "depth": self.DEFAULT_DEPTHTEXT_DEPTH}

        # pattern
        pa_selection = self.pattern_selection.get()
        pa_file_path = self.pattern_file_path
        if pa_selection == SettingsWindow.PATTERN_FILE:
            if not pa_file_path:
                self.chosen_pattern_label.config(fg=SettingsWindow.COLOR_ERROR)
                self.last_pattern_chosen.set("First select a file, please :)")
                return
            else:
                user_settings["pattern"] = pa_file_path
        elif pa_selection == SettingsWindow.PATTERN_DOTS:
            user_settings["pattern"] = "dots"
        elif pa_selection == SettingsWindow.PATTERN_RANDOM:
            user_settings["pattern"] = "R"

        # 3d mode
        user_settings["cross-eyed"] = False if self.mode_selection.get() == SettingsWindow.MODE_WALLEYED else True

        # output file
        if self.output_filepath:
            user_settings["output"] = self.output_filepath
        else:
            if self.dont_save_variable.get():
                user_settings["output"] = ""
            else:
                self.chosen_outputname_label.config(fg=SettingsWindow.COLOR_ERROR)
                self.last_outputname_chosen.set("Select an output name please, kind sir")
                return

        # Advanced settings
        # Depthmap gaussian blur
        global SMOOTH_FACTOR
        SMOOTH_FACTOR = self.depthmap_smoothness_scale.get()
        # Depth multiplier

        print("""
Final Settings:
    Depthmap:   {},
    Pattern:    {},
    3D mode:    {},
    Output:     {}""".format(
            user_settings["depthmap"],
            user_settings["pattern"],
            ("Cross-eyed" if user_settings["cross-eyed"] else "Wall-eyed"),
            user_settings["output"]))

        self.window_root.destroy()


def receive_arguments_from_gui():
    """
    Use Gui interface to ask user for options

    Returns
    -------
    dict
        Options
    """
    global user_settings
    root = Tk()
    root.withdraw()
    w = SettingsWindow(root)
    root.wait_window(w.window_root)
    root.destroy()
    return user_settings


def main():
    opts = receive_arguments_from_gui()
    print("Generating...")
    i = make_stereogram(opts)
    print("Displaying...")
    show_img(i)
    if opts["output"] != "":
        print("Saving...")
        output = save_to_file(i, opts["output"])
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
