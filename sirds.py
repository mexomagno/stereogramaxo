#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from PIL import Image as im, ImageDraw as imd
from random import choice
import os

# Constantes
SIZE = (800,600)
PATTERN_FRACTION = 8.0
OVERSAMPLE = 1.8
SHIFT_RATIO = 0.3
DMFOLDER = "depth_maps"
PATTERNFOLDER = "patterns"
SAVEFOLDER = "saved"

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
				if choice([True,False]):
					i_pix[c,f]=choice([(255,0,0),(255,255,0),(200,0,255)])
	# Repetir relleno
	x = 0
	rect = (0,0,pattern_width,i.size[1])
	region = i.crop(rect)
	while x < i.size[0]:
		i.paste(region,(x,0,x+pattern_width,i.size[1]))
		x += pattern_width
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
	pattern, isimg = makeBackground(dm.size,patt)
	# Usar oversampling si el patrón es una imagen y no random dots
	if isimg:
		dm = dm.resize(((int)(dm.size[0]*OVERSAMPLE),(int)(dm.size[1]*OVERSAMPLE)))
		pattern = pattern.resize(((int)(pattern.size[0]*OVERSAMPLE),(int)(pattern.size[1]*OVERSAMPLE)))
	size = dm.size
	pattern_width = (int)(size[0]*1.0/PATTERN_FRACTION)
	pt_pix = pattern.load()
	dm_pix = dm.load()
	# Recorre mapa de profundidad y modifica el patrón
	for f in range(size[1]):
		for c in range(pattern_width,pattern.size[0]):
			# Leer depthmap y obtener shift
			ponderador=pattern_width*SHIFT_RATIO # Empíricamente, en un sitio pasaban de 120px en el punto más profundo a 90px (25%)
			shift  = (dm_pix[(c-pattern_width),f] if mode == "we" else (255-dm_pix[(c-pattern_width),f]))/255.0*ponderador
			"""
				Leo depthmap
				mapeo profundidad a cantidad de shifteo. depth 255 es shifteo máximo (50%% del ancho del patrón?)
				Shifteo desde la derecha todos los pixeles, hacia la izquierda, una cantidad establecida por el shift calculado.
			"""
			# Shiftear pixeles
			pt_pix[c,f]=pt_pix[c-pattern_width+shift,f]
	# Retorna stereograma
	if isimg:
		pattern = pattern.resize(((int)(pattern.size[0]/OVERSAMPLE),(int)(pattern.size[1]/OVERSAMPLE)),im.LANCZOS) # NEAREST, BILINEAR, BICUBIC, LANCZOS
	return pattern

def makeDepthText(text, depth=50,fontsize=50, font="freefont/FreeSansBold"):
	"""
	Recibe: Texto, profundidad de 0 a 100 y fontsize. 
	Retorna: depth map (imagen).
	Esta función genera un mapa de profundidad con un texto, para generar stereograma a partir de él.
	"""
	import ImageFont as imf
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

def saveToFile(img,name,format="",savefolder = SAVEFOLDER):
	# Chequear que carpeta de guardado existe, sino, crearla
	if not os.path.exists(savefolder):
		try:
			os.mkdir(savefolder)
		except IOError, msg:
			print ("No se puede crear archivo: {}".format(msg))
			exit(1)
	valid_ext = ['png','jpeg','bmp','eps','gif','jpg','im','msp','pcx','ppm','spider','tiff','webp','xbm']
	# Tres formas de especificar formato: Con nombre de archivo, poniendo "format" y con el formato default de la imagen
	# Prioridades son: Nombre de archivo, parámetro format, formato interno de imagen
	# Intentar guardar con formato de nombre
	filename = name[0:(len(name)-len(fileformat)-1)] if name.find(".")>0 else name	# nombre sin extensión
	fileformat = name.strip().split('.')[-1].lower() if name.find(".")>0 else ""# Extensión sola
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
		return finalname
	except IOError, msg:
		print("Error al guardar imagen como '{}': {}".format(filename,msg))
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
	import sys
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

def main():
	opts = checkArgs()
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
		if output != None:
			print("Imagen guardada como '{}'".format(output))
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


PENDIENTE:


Diseño de argumentos:
	Opción R es Random. Elige de los que ya existen.
	-f -d --depthmap <filename>|R	: Especifica path al depthmap a usar
	-p --pattern <filename>|dots|R	: Especifica path al patrón a usar o si quiere puntos
	-h --help	: Muestra ayuda. Se ignora el resto de las opciones.
	-R --random : Equivalente a --depthmap R --pattern R
	-o <filename> : Guarda archivo generado como "filename". La extensión de este parámetro especifica el formato. De no incluirse, se usa la default 'png'.
	-m --mode : Modo wall-eyed o cross-eyed (we, ce). El típico es wall-eyed.
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