#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
# This "PIL" refers to Pillow, the PIL fork. Check https://pillow.readthedocs.io/en/3.3.x
from PIL import Image as im, ImageDraw as imd
from random import choice
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
                if choice([True,False,False,False]):
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

def showHelp(mensaje = ""):
    helptext = "USO: asstoasstoass"
    if mensaje!="":
        helptext = "Error: {}\n\n{}".format(mensaje,helptext)
    print(helptext)
    exit(0)

def checkArgs():
    """
        Retorna tupla con opciones:
            (depthmap = <filename>,
             pattern  = <filename>,
             output   = <filename>)
        En caso de encontrar opción "help", inmediatamente se muestra ayuda y se deja de parsear.
        En caso de especificar --random, queda claro en "depthmap" y "pattern".
    """
    valid_args = {	"depthmap"	:["-d","-f","-dm","--depthmap","--depth-map"], 	# Parámetro: Nombre de archivo
                    "pattern"	:["-p","--pattern"],							# Parámetro: Nombre de archivo
                    "output"	:["-o","--output"],								# Parámetro: Nombre de archivo
                    "cross-eyed":["-ce","--cross-eyed"],						# Parámetro: Nada
                    "random"	:["--random","-R"],								# Parámetro: Nada
                    "help"		:["-h","--help","-?"]}							# Parámetro: Nada
    already_set= {	"depthmap"	: False,
                    "pattern"	: False,
                    "output"	: False,
                    "cross-eyed": False}
    # Comportamiento default
    opts = {	"depthmap"	:"",		# Sin especificar
                "pattern"	:"dots",	# Patrón de puntos
                "output"	:"",		# Sin especificar
                "cross-eyed":False}		# Wall-eyed
    args = sys.argv
    # Checkear que argumentos son válidos
    # 	- Ver que argumento es válido
    #	- Ver que parámetro del argumento existe y es válido
    i=1 # Indice del argumento
    while i < len(args):
        if args[i] in valid_args["help"]:
            showHelp()
        if args[i] in valid_args["random"]:
            if already_set["depthmap"] or already_set["pattern"]:
                showHelp("Múltiple definición para 'depthmap' y/o 'pattern'")
            opts["depthmap"] = opts["pattern"] = "R"
            already_set["depthmap"] = already_set["pattern"] = True
            i+=1
            continue
        if args[i] in valid_args["cross-eyed"]:
            if already_set["cross-eyed"]:
                showHelp("Múltiple declaración para '{}'".format(args[i]))
            opts["cross-eyed"] = True
            already_set["cross-eyed"] = True
            i+=1
            continue
        # Si no es argumento válido
        if args[i] not in (valid_args["depthmap"]+valid_args["pattern"]+valid_args["output"]):
            showHelp("Argumento desconocido: '{}'".format(args[i]))
        # Si no entregó parámetro para el argumento, error
        if i == len(args)-1 or args[i+1] in (valid_args["depthmap"]+valid_args["pattern"]+valid_args["output"]+valid_args["random"]+valid_args["help"]+valid_args["cross-eyed"]):
            showHelp("Debe especificar parámetro para '{}'".format(args[i]))
        # Ver qué parámetro se está seteando
        for opt in ["depthmap","pattern","output"]:
            if args[i] in valid_args[opt]:
                if already_set[opt]:
                    showHelp("Múltiple declaración para '{}'".format(args[i]))
                opts[opt] = args[i+1]
                already_set[opt] = True
                break
        i+=2
    return opts

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
    # DEFAULTS
    DEFAULT_DEPTHMAP_SELECTION = DEPTHMAP_SHARK
    DEFAULT_PATTERN_SELECTION = PATTERN_DOTS
    DEFAULT_MODE_SELECTION = MODE_WALLEYED
    DEFAULT_DONTSAVE_VALUE = False
    DEFAULT_DEPTHMAP_FILE = "depth_maps/tiburon.png"
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
        self.window_root.geometry("+{}+{}".format(SettingsWindow.WINDOW_POSITION_X, SettingsWindow.WINDOW_POSITION_Y))
        self.window_root.title = "Settings"
        main_frame = Frame(self.window_root)
        main_frame.pack()
        # main elements
        depthmap_frame = Frame(self.window_root)
        depthmap_frame.pack()
        pattern_frame = Frame(self.window_root)
        pattern_frame.pack()
        mode_frame = Frame(self.window_root)
        mode_frame.pack()
        outputname_frame = Frame(self.window_root)
        outputname_frame.pack()
        # fonts
        section_title_font = tkFont.Font(family="Helvetica", size = 12, weight ="bold")
        chosen_file_font = tkFont.Font(family="Helvetica", size=10)

        # depthmap settings
        choose_depthmap_label = Label(depthmap_frame, text = "Depthmap selection", font=section_title_font)
        choose_depthmap_label.pack()
        self.depthmap_selection = IntVar()
        self.depthmap_selection.set(SettingsWindow.DEFAULT_DEPTHMAP_SELECTION)
        for text, option in SettingsWindow.DEPTHMAP_OPTIONS:
            b = Radiobutton(depthmap_frame, text = text, variable = self.depthmap_selection, value = option, command=self.updateDepthmapBrowseButton)
            b.pack(anchor = NW, side = LEFT)
        self.depthmap_browse_button = Button(depthmap_frame, text = "Browse...", command = self.askOpenDepthmapFile, state=DISABLED)
        self.depthmap_browse_button.pack(anchor = NW, side = LEFT)
        self.last_depthmap_chosen = StringVar()
        self.last_depthmap_chosen.set("")
        self.chosen_depthmap_label = Label(depthmap_frame, textvariable=self.last_depthmap_chosen, font=chosen_file_font, fg=SettingsWindow.COLOR_CHOSEN_FILE)
        self.chosen_depthmap_label.pack()

        # Pattern settings
        choose_pattern_label = Label(pattern_frame, text = "Pattern selection", font=section_title_font)
        choose_pattern_label.pack()
        self.pattern_selection = IntVar()
        self.pattern_selection.set(SettingsWindow.DEFAULT_PATTERN_SELECTION)
        for text, option in SettingsWindow.PATTERN_OPTIONS:
            b = Radiobutton(pattern_frame, text = text, variable = self.pattern_selection, value = option, command=self.updatePatternBrowseButton)
            b.pack(anchor = NW, side = LEFT)
        self.pattern_browse_button = Button(pattern_frame, text = "Browse...", command = self.askOpenPatternFile, state=DISABLED)
        self.pattern_browse_button.pack(anchor = NW, side = LEFT)
        self.last_pattern_chosen = StringVar()
        self.last_pattern_chosen.set("")
        self.chosen_pattern_label = Label(pattern_frame, textvariable= self.last_pattern_chosen, font=chosen_file_font, fg=SettingsWindow.COLOR_CHOSEN_FILE)
        self.chosen_pattern_label.pack()

        # Mode selection
        choose_mode_label = Label(mode_frame, text = "3D Viewing Mode", font=section_title_font)
        choose_mode_label.pack()
        self.mode_selection = IntVar()
        self.mode_selection.set(SettingsWindow.DEFAULT_MODE_SELECTION)
        b = Radiobutton(mode_frame, text = "Wall-eyed", variable = self.mode_selection, value = SettingsWindow.MODE_WALLEYED, indicatoron=0)
        b.pack(side = LEFT)
        b.select()
        b2 = Radiobutton(mode_frame, text = "Cross-eyed", variable = self.mode_selection, value = SettingsWindow.MODE_CROSSEYED, indicatoron=0)
        b2.pack(side = LEFT)

        # output filename
        outputname_label = Label(outputname_frame, text = "Saving", font=section_title_font)
        outputname_label.pack()
        self.save_button = Button(outputname_frame, text="Save as...", command=self.askSaveAs)
        self.save_button.pack()
        self.last_outputname_chosen = StringVar()
        self.last_outputname_chosen.set("")
        self.chosen_outputname_label = Label(outputname_frame, textvariable=self.last_outputname_chosen, font=chosen_file_font, fg=SettingsWindow.COLOR_CHOSEN_FILE)
        self.chosen_outputname_label.pack()
        self.dont_save_variable = BooleanVar()
        self.dont_save_variable.set(self.DEFAULT_DONTSAVE_VALUE)
        self.dont_save_checkbox = Checkbutton(outputname_frame, text="I don't wanna save it!", variable = self.dont_save_variable, command=self.updateSaveButton)
        self.dont_save_checkbox.pack()
        #
        b = Button(self.window_root, text = "Generate!", command = self.setUserSettings)
        b.pack(side = BOTTOM)

        self.depthmap_file_path = ""
        self.pattern_file_path = ""
        self.output_filepath = ""

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
                self.last_depthmap_chosen.set("SELECT A FUCKING FILE FIRST, PLEASE :)")
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
                self.last_pattern_chosen.set("SELECT A FUCKING FILE FIRST, PLEASE :)")
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
                self.last_outputname_chosen.set("Select an output name please Sir. Please.")
                return
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


def checkArgs2():
    """
    This method checks the input arguments using argparse, and returns a settings dictionary


Diseño de argumentos:
    Opción R es Random. Elige de los que ya existen.
    -f -d --depthmap <filename>|R	: Especifica path al depthmap a usar
    -p --pattern <filename>|dots|R	: Especifica path al patrón a usar o si quiere puntos
    -h --help	: Muestra ayuda. Se ignora el resto de las opciones.
    -R --random : Equivalente a --depthmap R --pattern R
    -o <filename> : Guarda archivo generado como "filename". La extensión de este parámetro especifica el formato. De no incluirse, se usa la default 'png'.
    -m --mode : Modo wall-eyed o cross-eyed (we, ce). El típico es wall-eyed.
    """

    parser = AP.ArgumentParser(
        description = "Yet another stereogram generator",
        epilog = "Version {}".format(PROGRAM_VERSION))
    parser.add_argument("-d", "--depthmap", nargs=1, metavar="DEPTHMAP",
                        help="""
                        Specifies the main 3D image's depthmap to be used. You can specify the absolute path to the file
                        or 'R' for a random image""")
    parser.add_argument("-p", "--pattern", nargs=1, type=str, metavar="PATTERN" ,
                        help="""
                        Specifies the image to use as a pattern. You can specify the file absolute path, 'R' for letting
                        the program choose one for you, or 'D' for a dot pattern
                        """)
    parser.add_argument("-r", "--random", action="store_true",
                        help="""
                        Use a random pattern and a random depthmap
                        """)
    parser.add_argument("-o", "--output", nargs=1, metavar="OUTPUT",
                        help="""
                        Specifies the output file name. Here you also define the file format. If no file format is
                        entered, {} will be used
                        """.format(DEFAULT_OUTPUT_FILE_FORMAT.upper()))
    parser.add_argument("-w", "--wall-eyed", nargs=1, metavar="3D_MODE",
                        help="""
                        Generates a Wall-eyed stereogram. If not specified, this mode will be used.
                        Incompatible with the -c option.
                        """)
    parser.add_argument("-c", "--cross-eyed", nargs=1, metavar="3D_MODE",
                        help="""
                        Generates a Cross-eyed stereogram. Incompatible with the -w option.
                        """)
    args = parser.parse_args()
    # CHECK ARGUMENTS
    print (vars(args))
    # if no parameters are specified, ask for depthmap:
    exit()



def main():
    opts = askUserForSettings()
    if opts["depthmap"] == "":
        showHelp("Debe especificar un archivo de mapa de profundidad!")
    #depthmap=makeDepthText("Chingeki", 60, 120)
    #saveToFile(depthmap,"chingeki.png")
    print("Generando...")
    i = makeStereogram(opts["depthmap"],opts["pattern"],("ce" if opts["cross-eyed"] else "we"))
    print("Mostrando...")
    showImg(i)
    if opts["output"] != "":
        print("Guardando...")
        output = saveToFile(i,opts["output"])
        if output == None:
            print("Oops! Couldn't save file!!")
    #from PIL import ImageFilter as imf
    #showImg(i.filter(imf.GaussianBlur(6)))
    #saveToFile(i,"guitarra.jpg")

if __name__ == "__main__":
    main()

"""
Problemas:
Cuando pasa de poco profundo a profundo, una parte de la superficie se repite hacia la derecha.
La explicación de internet es que son puntos que el ojo derecho no debería ser capaz de ver, pero los estamos considerando igual.
Es reparable... pero cómo?
Esto se llama Hidden Surface Removal.
"""



# Miembros de los objetos Image:
# 	format | Formato de la imagen (PNG, JPEG, BMP...)
# 	size | Tupla con tamaño de la imagen (x, y)
# 	mode | Sistema de color (RGB, CMYK, L (bco y negro), ...)


# Métodos importantes de Image:
#	(out) Image.new(modo, tamaño, color) | retorna imagen nueva con parámetros especificados.
#	show(<objeto>) | muestra la imagen
#	open(<archivo>) | Abre la imagen. Independiente de la extensión
#	save(<archivo>) | Guarda la imagen. Automáticamente intenta convertir si se setea un nombre con una extensión determinada. Se puede atrapar IOError si no se puede convertir. Se puede además entregar como segundo argumento un formato determinado.
#	thumbnail((sizex,sizey)) | Crea thumbnail 
# 	(region) crop((1x,1y,2x,2y)) | Corta rectángulo a partir de la 4 tupla que lo define. Retorna imagen recortada
# 	paste(region, caja(1x,1y,3x,2y)) | pega región. Puede recibir argumento de alpha (0 a 255).
#	(banda1, banda2, banda3) split() | divide imagen multibanda (RGB por ejemplo) en imágenes independientes. Retorna tupla.
#??? 	<region> transpose(<macro>) | Aplica cierta transformación. Transpose(ROTATE_90) es equivalente a rotate(90).
#	transform(<??>) | Forma general. Aplica transformación a imagen.
#	(out) resize((x,y)) | cambia tamaño. Retorna nueva imagen
# 	(out) rotate(<grados>) | Rota en sexagesimales. Retorna resultado.
#	(out) convert(<string de formato>) | Convierte entre formatos. Retorna resultado.
#   (banda1,banda2,banda3) getpixel((x, y)) | retorna un pixel
# 	putpixel((x,y), value) | modifica pixel. Value depende de las bandas. Lento, recomiendan usar módulo ImageDraw.
# 	(out) point(lookup_table, mode=None) | Mapea imagen aplicando lookup_table a los pixeles.
# Se pueden aplicar filtros
# Se pueden aplicar point operations 

# Macros
#	Image.FLIP_LEFT_RIGHT
#	Image.FLIP_TOP_BOTTOM
# 	Image.ROTATE_90
# 	Image.ROTATE_180
# 	Image.ROTATE_270

# Más info en http://pillow.readthedocs.org/handbook/tutorial.html

#### Para dibujar, existe el módulo ImageDraw.
# Hay que crear un objeto ImageDraw asociado a la imagen. Luego llamar los métodos.

# Métodos importantes:
# tiene para dibujar: line, ellipse, point, polygon, rectangle, pieslice, chord, bitmap, arc, shape, text, multiline_text, textsize.
# point((x,y), fill=None) | pixel en x, y de color fill, siguiendo formato soportado de colores de Pillow.