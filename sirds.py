#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
# This "PIL" refers to Pillow, the PIL fork. Check https://pillow.readthedocs.io/en/3.3.x
from PIL import Image as im, ImageDraw as imd
from random import choice, random
import os
import argparse as AP
# GUI
from Tkinter import *
import tkFileDialog, tkFont

# Program info
PROGRAM_VERSION="2.0"
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
SUPPORTED_OUTPUT_IMAGE_FORMATS = SUPPORTED_INPUT_IMAGE_FORMATS
DEFAULT_OUTPUT_FILE_FORMAT="png"

# Constantes
SIZE = (800,600)
PATTERN_FRACTION = 8.0
OVERSAMPLE = 1.8
SHIFT_RATIO = 0.3
DMFOLDER = "depth_maps"
PATTERNFOLDER = "patterns"
SAVEFOLDER = "saved"
LEFT_TO_RIGHT = False # True: Recorre de izq. a derecha. False: Recorre desde el centro a los bordes.
DOT_DRAW_PROBABILITY=0.4 # Decides how often a random dot is drawn
SMOOTH_DEPTHMAP = True
SMOOTH_FACTOR = 1.8

def showImg(i):
    i.show(command="eog")

def makeBackground(size = SIZE,filename=""):
    pattern_width = (int)(size[0]/PATTERN_FRACTION)
    # Patrón es un poco más largo que imagen original, para que quepa toda en 3D
    i = im.new("RGB", (size[0]+pattern_width,size[1]), color="black")
    i_pix = i.load()
    # Cargar desde imagen
    imagen = False
    if filename!="" and filename!="dots":
        pattern = loadFile((getRandom("pattern") if filename == "R" else filename))
        if pattern == None:
            print ("Error al cargar '{}'. Generando con puntos aleatorios.".format(filename))
            filename=""
        else:
            imagen = True
            pattern = pattern.resize((pattern_width,(int)((pattern_width*1.0/pattern.size[0])*pattern.size[1])),im.LANCZOS)
            # repetir verticalmente
            region = pattern.crop((0,0,pattern.size[0],pattern.size[1]))
            y = 0
            while y < i.size[1]:
                i.paste(region,(0,y,pattern.size[0],y+pattern.size[1]))
                y += pattern.size[1]
    # Relleno random
    if filename=="" or filename=="dots":
        for f in range(i.size[1]):
            for c in range(pattern_width):
                if random() < DOT_DRAW_PROBABILITY: #choice([True,False,False,False]):
                    i_pix[c,f]=choice([(255,0,0),(255,255,0),(200,0,255)])
    # Repetir relleno
    # x = 0
    # rect = (0,0,pattern_width,i.size[1])
    # region = i.crop(rect)
    # while x < i.size[0]:
    # 	i.paste(region,(x,0,x+pattern_iwdth,i.size[1]))
    # 	x += pattern_width
    return i,imagen

def getRandom(whatfile="depthmap"):
    """
        retorna nombre de archivo aleatorio.
        "whatfile" especifica si se quiere un 'depthmap' aleatorio o un 'pattern' aleatorio.
    """
    folder = (DMFOLDER if whatfile == "depthmap" else PATTERNFOLDER)
    return folder + "/" + choice(os.listdir(folder))

def makeStereogram(filename,patt="",mode="we"):
    """
    Recibe: Depth Map, patrón a usar, modo {we,ce} (wall-eyed, cross-eyed)
    Retorna: Nada. El resultado está en la imagen recibida.

    Esta función hace la pega de generar el stereograma.
    Lee desde un depth map, genera el patrón de puntos y retorna la imagen con el stereograma.

    """
    # Cargar depthmap
    dm = loadFile((getRandom("depthmap") if filename == "R" else filename),'L')
    if (dm == None):
        print("Abortando")
        exit(1)
    if SMOOTH_DEPTHMAP:
        from PIL import ImageFilter as imf
        dm = dm.filter(imf.GaussianBlur(SMOOTH_FACTOR))

    # Crear patrón base
    background, isimg = makeBackground(dm.size,patt)
    # Usar oversampling si el patrón es una imagen y no random dots
    if isimg:
        dm = dm.resize(((int)(dm.size[0]*OVERSAMPLE),(int)(dm.size[1]*OVERSAMPLE)))
        background = background.resize(((int)(background.size[0]*OVERSAMPLE),(int)(background.size[1]*OVERSAMPLE)))
    size = dm.size
    pattern_width = (int)(size[0]*1.0/PATTERN_FRACTION)
    pt_pix = background.load()
    dm_pix = dm.load()
    ponderador=pattern_width*SHIFT_RATIO # Empíricamente, en un sitio pasaban de 120px en el punto más profundo a 90px (25%)
    # mover patrón al medio hacia la izquierda
    if not LEFT_TO_RIGHT:
        x_medios_bg = background.size[0]/2
        rect = (0,0,pattern_width,background.size[1])
        background.paste(background.crop(rect),(x_medios_bg-pattern_width,0,x_medios_bg,background.size[1]))
    for f in range(size[1]):
        if LEFT_TO_RIGHT:
            for c in range(pattern_width,background.size[0]):
                # De izquierda a derecha
                shift  = (dm_pix[(c-pattern_width),f] if mode == "we" else (255-dm_pix[(c-pattern_width),f]))/255.0*ponderador
                pt_pix[c,f]=pt_pix[c-pattern_width+shift,f]
        else:
            for c in range(x_medios_bg,background.size[0]):
                # Hacia el lado derecho
                shift  = (dm_pix[(c-pattern_width),f] if mode == "we" else (255-dm_pix[(c-pattern_width),f]))/255.0*ponderador
                pt_pix[c,f]=pt_pix[c-pattern_width+shift,f]
            for c in range(x_medios_bg-1,pattern_width-1,-1):
                # Hacia la izquierda
                shift  = (dm_pix[c,f] if mode == "we" else (255-dm_pix[c,f]))/255.0*ponderador
                pt_pix[c,f]=pt_pix[c+pattern_width-shift,f]
    if not LEFT_TO_RIGHT:
        background.paste(background.crop((pattern_width,0,2*pattern_width,background.size[1])),rect)
    #Retorna stereograma
    if isimg: # Regresa del oversampling
        background = background.resize(((int)(background.size[0]/OVERSAMPLE),(int)(background.size[1]/OVERSAMPLE)),im.LANCZOS) # NEAREST, BILINEAR, BICUBIC, LANCZOS
    return background

def makeDepthText(text, depth=50,fontsize=50, font="freefont/FreeSansBold"):
    """
    Recibe: Texto, profundidad de 0 a 100 y fontsize.
    Retorna: depth map (imagen).
    Esta función genera un mapa de profundidad con un texto, para generar stereograma a partir de él.
    """
    import PIL.ImageFont as imf
    if depth<0: depth=0
    if depth>100: depth=100
    fontroot="/usr/share/fonts/truetype"
    fontdir="{}/{}.ttf".format(fontroot,font)
    # Crear imagen (escala de grises)
    i=im.new('L',SIZE, "black")
    # Dibujar texto con gris apropiado
    fnt=imf.truetype(fontdir,fontsize)
    imd.Draw(i).text(((i.size[0]/2-len(text)/2*fontsize),(i.size[1]/2-fontsize)),text,font=fnt,fill=((int)(255.0*depth/100)))
    # Retornar imagen
    return i

def saveToFile(img,name,format=""):
    valid_ext = []
    for ext in SUPPORTED_OUTPUT_IMAGE_FORMATS:
        valid_ext.append(ext[1].split(".")[1].lower())
    print (valid_ext)
    # Tres formas de especificar formato: Con nombre de archivo, poniendo "format" y con el formato default de la imagen
    # Prioridades son: Nombre de archivo, parámetro format, formato interno de imagen
    # Intentar guardar con formato de nombre
    filename, fileformat = os.path.splitext(os.path.basename(name))
    fileformat = fileformat.replace(".","")
    dirname = os.path.dirname(name)
    if dirname == "":
        savefolder = SAVEFOLDER
    else:
        savefolder = dirname
    # Chequear que carpeta de guardado existe, sino, crearla
    if not os.path.exists(savefolder):
        try:
            os.mkdir(savefolder)
        except IOError, msg:
            print("No se puede crear archivo: {}".format(msg))
            exit(1)
    if fileformat not in valid_ext:
        # Intentar con formato especificado por parámetro
        fileformat = format
        if fileformat not in valid_ext:
            # Usar extensión con la que ya venía la imagen
            fileformat = img.format
            if fileformat not in valid_ext:
                fileformat = valid_ext[0]
    try:
        finalname = filename+"."+fileformat
        # Revisar que archivo no exista
        i=1
        while os.path.exists(savefolder+"/"+finalname):
            if i==1:
                print ("AVISO: Archivo '{}' ya existe en '{}'".format(finalname,savefolder))
            finalname = "{} ({}).{}".format(filename,i,fileformat)
            i+=1
        r = img.save(savefolder+"/"+finalname)
        print("Saved file as '{}/{}'".format(savefolder, finalname))
        return finalname
    except IOError, msg:
        print("Error al guardar imagen como '{}/{}': {}".format(savefolder,filename,msg))
        return None

def loadFile(name,type=''):
    try:
        i = im.open(name)
        if type != "":
            i = i.convert(type)
        #print ("Abierto '{}'. Formato: {}, Tamaño: {}, Bandas: {}".format(name, i.format, i.size, len(i.split())))
        # import numpy
        # print (numpy.array(i))
    except IOError, msg:
        print ("No se pudo abrir la imagen '{}': {}".format(name,msg))
        return None
    return i

user_settings = dict()

class SettingsWindow:
    # CONSTANTS
    DEPTHMAP_RANDOM = 0
    DEPTHMAP_SHARK = 1
    DEPTHMAP_FILE = 2
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
    COLOR_CHOSEN_FILE ="#002288"
    FONT_SECTION_TITLE = {"family":"Helvetica", "size":12, "weight":"bold"}
    FONT_CHOSEN_FILE = {"family":"Helvetica", "size":10, "weight":"normal"}
    FONT_GENERATE_BUTTON = {"family":"Helvetica", "size":13, "weight":"bold"}
    FONT_SECTION_SUBTITLE = {"family":"Helvetica", "size": FONT_SECTION_TITLE["size"]-2, "weight":"bold"}
    # DEFAULTS
    DEFAULT_DEPTHMAP_SELECTION = DEPTHMAP_SHARK
    DEFAULT_PATTERN_SELECTION = PATTERN_DOTS
    DEFAULT_MODE_SELECTION = MODE_WALLEYED
    DEFAULT_DONTSAVE_VALUE = False
    DEFAULT_DEPTHMAP_FILE = "depth_maps/tiburon.png"
    DEFAULT_DEPTH_MULTIPLIER = 1
    DEFAULT_DEPTHMAP_GAUSSIAN_BLUR = 0
    DEPTHMAP_OPTIONS = [
        ("Shark", DEPTHMAP_SHARK),
        ("Random", DEPTHMAP_RANDOM),
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
        depthmap_frame.pack(anchor=E)
        pattern_frame = Frame(self.window_root)
        pattern_frame.pack(anchor=E)
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
        b = Button(self.window_root, text = "Generate!", command = self.setUserSettings, font=self.FONT_GENERATE_BUTTON, bg = generate_button_bg_color, fg=generate_button_fg_color)
        b.pack(side = BOTTOM)

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
            b = Radiobutton(root, text=text, variable=self.depthmap_selection, value=option,
                            command=self.updateDepthmapBrowseButton)
            b.pack(anchor=NW, side=LEFT)
        self.depthmap_browse_button = Button(root, text="Browse...", command=self.askOpenDepthmapFile,
                                             state=DISABLED)
        self.depthmap_browse_button.pack(side=LEFT)
        self.last_depthmap_chosen = StringVar()
        self.last_depthmap_chosen.set("")
        self.chosen_depthmap_label = Label(root, textvariable=self.last_depthmap_chosen,
                                           font=self.makeFont(self.FONT_CHOSEN_FILE),
                                           fg=self.COLOR_CHOSEN_FILE)
        self.chosen_depthmap_label.pack()
    def addPatternSettings(self, root):
        self.newSectionTitle(root, "Pattern selection").pack()
        self.pattern_selection = IntVar()
        self.pattern_selection.set(self.DEFAULT_PATTERN_SELECTION)
        for text, option in self.PATTERN_OPTIONS:
            b = Radiobutton(root, text=text, variable=self.pattern_selection, value=option,
                            command=self.updatePatternBrowseButton)
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

    def addAdvancedSettings(self, root):
        self.newSectionTitle(root, "Advanced Settings").pack()
        # Depthmap smoothness
        depthmap_smoothness_frame = Frame(root)
        depthmap_smoothness_frame.pack(anchor=E)
        Label(depthmap_smoothness_frame, text = "Depthmap gaussian blur level", font=self.makeFont(self.FONT_SECTION_SUBTITLE)).pack(side=LEFT)
        self.depthmap_smoothness_scale = Scale(depthmap_smoothness_frame, from_=0, to=10, orient=HORIZONTAL, resolution=0.1)
        self.depthmap_smoothness_scale.pack(side=LEFT)
        self.depthmap_smoothness_scale.set(self.DEFAULT_DEPTHMAP_GAUSSIAN_BLUR)
        # Depth multiplirer
        depth_multiplier_frame = Frame(root)
        depth_multiplier_frame.pack(anchor=E)
        Label(depth_multiplier_frame, text="Depth multiplier", font=self.makeFont(self.FONT_SECTION_SUBTITLE)).pack(side=LEFT)
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
        self.filename = tkFileDialog.askopenfilename(initialdir=os.path.expanduser("~/Desktop"), filetypes = (SUPPORTED_INPUT_IMAGE_FORMATS + [("Show all files", "*")]))
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

    def updateBrowseButton(self, which):
        if which == "d":
            if self.depthmap_selection.get() == SettingsWindow.DEPTHMAP_FILE:
                self.depthmap_browse_button["state"] = NORMAL
            else:
                self.depthmap_browse_button["state"] = DISABLED
                # Clear last file selection
                self.last_depthmap_chosen.set("")
                self.depthmap_file_path = ""
        elif which == "p":
            if self.pattern_selection.get() == SettingsWindow.PATTERN_FILE:
                self.pattern_browse_button["state"] = NORMAL
            else:
                self.pattern_browse_button["state"] = DISABLED
                # Clear last file selection
                self.last_pattern_chosen.set("")
                self.pattern_file_path = ""


    def updateDepthmapBrowseButton(self):
        self.updateBrowseButton("d")

    def updatePatternBrowseButton(self):
        self.updateBrowseButton("p")

    def setUserSettings(self):
        global user_settings
        # Get settings and update user_settings
        user_settings = {}
        # depthmap
        dm_selection = self.depthmap_selection.get()
        dm_file_path = self.depthmap_file_path
        if dm_selection == SettingsWindow.DEPTHMAP_FILE:
            if not dm_file_path:
                self.chosen_depthmap_label.config(fg = SettingsWindow.COLOR_ERROR)
                self.last_depthmap_chosen.set("First select a file, please :)")
                return
            else:
                user_settings["depthmap"] = dm_file_path
        elif dm_selection == SettingsWindow.DEPTHMAP_SHARK:
            user_settings["depthmap"] = SettingsWindow.DEFAULT_DEPTHMAP_FILE
        elif dm_selection == SettingsWindow.DEPTHMAP_RANDOM:
            user_settings["depthmap"] = "R"

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

def askUserForSettings():
    global user_settings
    root = Tk()
    root.withdraw()
    w = SettingsWindow(root)
    root.wait_window(w.window_root)
    root.destroy()
    return user_settings

def main():
    opts = askUserForSettings()
    print("Generando...")
    i = makeStereogram(opts["depthmap"],opts["pattern"],("ce" if opts["cross-eyed"] else "we"))
    print("Mostrando...")
    showImg(i)
    if opts["output"] != "":
        print("Guardando...")
        output = saveToFile(i,opts["output"])
        if output == None:
            print("Oops! Couldn't save file!!")

if __name__ == "__main__":
    main()

"""
Problemas:
Cuando pasa de poco profundo a profundo, una parte de la superficie se repite hacia la derecha.
La explicación de internet es que son puntos que el ojo derecho no debería ser capaz de ver, pero los estamos considerando igual.
Es reparable... pero cómo?
Esto se llama Hidden Surface Removal.
"""

# TODO: Uncouple strings and common definitions, remove hardcoded messages... that sort of stuff
# TODO: Translate everything to english
# TODO: Add Text generation option
# TODO: Expand grayscale between the two extremes (enhances near-flat depth maps)
# TODO: Try to enlarge grayscale depth
# TODO: Show advanced menu
# TODO: Make random pattern option include dots
# TODO: Fix Cross-eyed bug