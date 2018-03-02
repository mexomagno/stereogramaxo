#!/usr/bin/python
# coding: utf-8
import os
import sys
import json
import time
import argparse
from random import choice, random
# This "PIL" refers to Pillow, the PIL fork. Check https://pillow.readthedocs.io/en/3.3.x
from PIL import Image as im
from PIL import ImageDraw as imd
from PIL import ImageFilter as imflt
from PIL import ImageFont as imf

# Program info
PROGRAM_VERSION = "2.0"

# Default Values
# SUPPORTED_INPUT_IMAGE_FORMATS = [
#     ("PNG", "*.png"),
#     ('JPEG', "*.jpeg"),
#     ("Bitmap", "*.bmp"),
#     ("EPS", "*.eps"),
#     ("GIF", "*.gif"),
#     ("JPG", "*.jpg"),
#     ("IM", "*.im"),
#     ("MSP", "*.msp"),
#     ("PCX", "*.pcx"),
#     ("PPM", "*.ppm"),
#     ("Spider", "*.spider"),
#     ("TIFF", "*.tiff"),
#     ("WEBP", "*.webp"),
#     ("XBM", "*.xbm")
# ]
SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpeg", ".bmp", ".eps", ".gif", ".jpg", ".im", ".msp", ".pcx", ".ppm", ".spider", ".tiff", ".webp", ".xbm"]
DEFAULT_DEPTHTEXT_FONT = "freefont/FreeSansBold"
DEFAULT_OUTPUT_EXTENSION = SUPPORTED_IMAGE_EXTENSIONS[0]
# CONSTANTS
DMFOLDER = "depth_maps"
PATTERNFOLDER = "patterns"
SAVEFOLDER = "saved"

# SETTINGS
SIZE = (800, 600)  # px
MAX_DIMENSION = 1500  # px
PATTERN_FRACTION = 8.0
OVERSAMPLE = 1.8
SHIFT_RATIO = 0.3
LEFT_TO_RIGHT = False  # Defines how the pixels will be shifted (left to right or center to sides)
DOT_DRAW_PROBABILITY = 0.4  # Decides how often a random dot is drawn
SMOOTH_FACTOR = 1.8
DOT_OVER_PATTERN_PROBABILITY = 0.3  # Defines how often dots are chosen over pattern on random pattern selection

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


def redistribute_grays(img_object, gray_height):
    """
    For a grayscale depthmap, compresses the gray range to be between 0 and the max gray height

    Parameters
    ----------
    img_object : PIL.Image.Image
        The open image
    gray_height : float
        Max gray. 0 = black. 1 = white.

    Returns
    -------
    PIL.Image.Image
        Modified image object
    """
    if img_object.mode != "L":
        img_object = img_object.convert("L")
    # Determine min and max gray value
    min_gray = {
        "point": (0, 0),
    }
    min_gray["value"] = img_object.getpixel(min_gray["point"])
    max_gray = {
        "point": (0, 0),
    }
    max_gray["value"] = img_object.getpixel(max_gray["point"])

    for x in range(img_object.size[0]):
        for y in range(img_object.size[1]):
            this_gray = img_object.getpixel((x, y))
            if this_gray > img_object.getpixel(max_gray["point"]):
                max_gray["point"] = (x, y)
                max_gray["value"] = this_gray
            if this_gray < img_object.getpixel(min_gray["point"]):
                min_gray["point"] = (x, y)
                min_gray["value"] = this_gray

    # Transform to new scale
    old_min = min_gray["value"]
    old_max = max_gray["value"]
    old_interval = old_max - old_min
    new_min = 0
    new_max = int(255.0 * gray_height)
    new_interval = new_max - new_min

    conv_factor = float(new_interval)/float(old_interval)

    pixels = img_object.load()
    for x in range(img_object.size[0]):
        for y in range(img_object.size[1]):
            pixels[x, y] = int((pixels[x, y] * conv_factor)) + new_min
    return img_object


def make_stereogram(parsed_args):
    """
    Actually generates the stereogram.

    Parameters
    ----------
    parsed_args : Namespace
        Parsed options

    Returns
    -------
    PIL.Image.Image :
        Generated stereogram image
    """
    # Load stereogram depthmap
    if parsed_args.text:
        dm = make_depth_text(parsed_args.text, DEFAULT_DEPTHTEXT_FONT)
    else:
        dm = load_file(parsed_args.depthmap, 'L')
    if dm is None:
        print("Aborting")
        exit(1)

    # Apply gaussian blur filter
    dm = dm.filter(imflt.GaussianBlur(parsed_args.blur))


    # Redistribute grayscale range
    if parsed_args.text:
        dm = redistribute_grays(dm, parsed_args.forcedepth if parsed_args.forcedepth is not None else 0.5)
    elif parsed_args.forcedepth:
        dm = redistribute_grays(dm, parsed_args.forcedepth)


    # Create base pattern
    background, isimg = make_background(dm.size, "" if parsed_args.dots else parsed_args.pattern)
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
                this_x = min(max(c - pattern_width, 0), size[0]-1)
                shift = (dm_pix[this_x, f] if parsed_args.wall else (255 - dm_pix[this_x, f])) / 255.0 * ponderador
                pt_pix[c, f] = pt_pix[c - pattern_width + shift, f]
        else:
            for c in range(x_medios_bg, background.size[0]):
                # Center to right
                this_x = min(max(c - pattern_width, 0), size[0]-1)
                shift = (dm_pix[this_x, f] if parsed_args.wall else (255 - dm_pix[this_x, f])) / 255.0 * ponderador
                pt_pix[c, f] = pt_pix[c - pattern_width + shift, f]
            for c in range(x_medios_bg - 1, pattern_width - 1, -1):
                # Center to left
                shift = (dm_pix[c, f] if parsed_args.wall else (255 - dm_pix[c, f])) / 255.0 * ponderador
                pt_pix[c, f] = pt_pix[c + pattern_width - shift, f]
    if not LEFT_TO_RIGHT:
        background.paste(background.crop((pattern_width, 0, 2 * pattern_width, background.size[1])), rect)
    if isimg:  # Return from oversampled image
        background = background.resize(((int)(background.size[0] / OVERSAMPLE), (int)(background.size[1] / OVERSAMPLE)),
                                       im.LANCZOS)  # NEAREST, BILINEAR, BICUBIC, LANCZOS
    return background


def make_depth_text(text, font=DEFAULT_DEPTHTEXT_FONT):
    """
    Makes a text depthmap

    Parameters
    ----------
    text : str
        Text to generate
    font : str
        Further font specification

    Returns
    -------
    PIL.Image.Image
        Generated depthmap image
    """
    fontroot = "/usr/share/fonts/truetype"
    fontdir = "{}/{}.ttf".format(fontroot, font)
    # Create image (grayscale)
    i = im.new('L', SIZE, "black")
    # Draw text with appropriate gray level
    font_size = 1
    fnt = imf.truetype(fontdir, font_size)
    while fnt.getsize(text)[0] < SIZE[0]*0.9 and fnt.getsize(text)[1] < SIZE[1]*0.9:
        font_size += 1
        fnt = imf.truetype(fontdir, font_size)
    imd.Draw(i).text(
        ((SIZE[0] / 2 - fnt.getsize(text)[0] / 2,
          SIZE[1] / 2 - fnt.getsize(text)[1] / 2)),
        text, font=fnt,
        fill=((int)(255.0)))
    return i


def save_to_file(img_object):
    file_ext = DEFAULT_OUTPUT_EXTENSION
    # Trying to save with image name format
    savefolder = SAVEFOLDER
    # Try to create folder, if it doesn't exist already
    if not os.path.exists(savefolder):
        try:
            os.mkdir(savefolder)
        except IOError as e:
            print("Cannot create file: {}".format(e))
            exit(1)
    try:
        outfile_name = u"{date}{ext}".format(
            date=time.strftime("%Y%m%d-%H%M%S", time.localtime()),
            ext=file_ext
        )
        out_path = os.path.join(savefolder, outfile_name)
        r = img_object.save(out_path)
        print "Saved file in {}".format(out_path)
        return out_path
    except IOError as e:
        print("Error trying to save image: {}".format(e))
        return None


def load_file(name, type=''):
    try:
        i = im.open(name)
        if type != "":
            i = i.convert(type)
    except IOError, msg:
        print("Picture couln't be loaded '{}': {}".format(name, msg))
        return None
    # Resize if too big
    if max(i.size) > MAX_DIMENSION:
        max_dim = 0 if i.size[0] > i.size[1] else 1
        old_max = i.size[max_dim]
        new_max = MAX_DIMENSION
        factor = new_max/float(old_max)
        print "Image is big: {}. Resizing by a factor of {}".format(i.size, factor)
        i = i.resize((int(i.size[0]*factor), int(i.size[1]*factor)))
    return i


def obtain_args():
    """
    Retrieves arguments and parses them to a dict.
    """
    def _restricted_depth(x):
        x = float(x)
        min = 0.0
        max = 1.0
        if x < min or x > max:
            raise argparse.ArgumentTypeError("{} not in range [{}, {}]".format(x, min, max))
        return x

    def _restricted_blur(x):
        x = int(x)
        min = 0
        max = 100
        if x < min or x > max:
            raise argparse.ArgumentTypeError("{} not in range [{}, {}]".format(x, min, max))
        return x

    def _supported_image_file(filename):
        if not os.path.exists(filename):
            raise argparse.ArgumentTypeError("File does not exist")
        _, ext = os.path.splitext(filename)
        if filename != "dots" and ext.strip().lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            raise argparse.ArgumentTypeError("File extension is not supported. Valid options are: {}".format(
                SUPPORTED_IMAGE_EXTENSIONS))
        return filename

    arg_parser = argparse.ArgumentParser(description="Stereogramaxo: An autostereogram generator, by Mexomagno")
    depthmap_arg_group = arg_parser.add_mutually_exclusive_group(required=True)
    depthmap_arg_group.add_argument("--depthmap", "-d", help="Path to a depthmap image file", type=_supported_image_file)
    depthmap_arg_group.add_argument("--text", "-t", help="Generate a depthmap with text", type=str)
    pattern_arg_group = arg_parser.add_mutually_exclusive_group(required=True)
    pattern_arg_group.add_argument("--dots", help="Generate a dot pattern for the background", action="store_true")
    pattern_arg_group.add_argument("--pattern", "-p", help="Path to an image file to use as background pattern",
                            type=_supported_image_file)
    viewmode_arg_group = arg_parser.add_mutually_exclusive_group(required=True)
    viewmode_arg_group.add_argument("--wall", "-w", help="Wall eyed mode", action="store_true")
    viewmode_arg_group.add_argument("--cross", "-c", help="Cross eyed mode", action="store_true")
    arg_parser.add_argument("--blur", "-b", help="Gaussian blur ammount", type=_restricted_blur, default=2)

    arg_parser.add_argument("--forcedepth", help="Force max depth to use", type=_restricted_depth)
    args = arg_parser.parse_args()
    print(args)
    return args


def main():
    parsed_args = obtain_args()
    print("Generating...")
    i = make_stereogram(parsed_args)
    show_img(i)
    return
    print "Saving..."
    output = save_to_file(i)
    if output is None:
        print "Error: Could not save to file"

if __name__ == "__main__":
    main()

"""
Problems:
When image sharply changes from one depth to a different one, a part of the surface edge repeats to the right and left.
Internet's explanation is that there are some points one eye shouldn't be able to see, but we nonetheless consider them
in the stereogram. They say it can be fixed... but how?
This is called Hidden Surface Removal.
"""

# TODO: Fix Cross-eyed bug
# TODO: Fix text left cropping
# TODO: Try to fix broken fin on shark (Hidden Surface Removal?)
# TODO: Provide options for dots settings
# TODO: Provide option to match pattern height
