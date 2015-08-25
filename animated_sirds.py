#!/usr/bin/python
# -*- coding: utf-8 -*-

from sirds import *

# Recibe carpeta con frames
# Aplica algoritmo a cada frame
# guarda cada frame resultante en carpeta nueva dentro de la anterior
# DESPUES: Crea video con frames

import os,sys

OUTFOLDER_SUFIX = "_animacion"
# checkear carpeta
if len(sys.argv)<=1:
	print "Debe ingresar carpeta!"
	exit(1)
folder = sys.argv[1]
print folder
if not os.path.exists(folder):
	print "Carpeta no existe"
	exit(1)
# Crear carpeta para resultados
if not os.path.exists(folder+OUTFOLDER_SUFIX):
	os.mkdir(folder+OUTFOLDER_SUFIX)
pattern = "patterns/jellybeans_tile.jpg"
count = 1
# Obtener archivos
dirlist = os.listdir(folder)
nfiles = len(dirlist)
for file in dirlist:
	if os.path.isdir(folder+"/"+file):
		continue
	i = makeStereogram(folder+"/"+file,pattern,"we")
	saveToFile(i,"frame_{}".format(count),savefolder = (folder+OUTFOLDER_SUFIX))
	print "{} de {} listos".format((count),nfiles)
	count+=1
print "Creando video..."
#os.chdir(folder+OUTFOLDER_SUFIX)
from subprocess import call
call(('ffmpeg -r 30 -f image2 -i '+folder+OUTFOLDER_SUFIX+'/frame_%d.png -crf 15 -vcodec libx264 '+folder+'_video.mp4').split(),stdout=open(os.devnull,'wb'))
print "Video creado como '{}_video.mp4'".format(folder)
print "Eliminando archivos temporales..."
for file in os.listdir(folder+OUTFOLDER_SUFIX):
	os.remove(folder+OUTFOLDER_SUFIX+"/"+file)
os.rmdir(folder+OUTFOLDER_SUFIX)
print "Listo"
