#!/usr/bin/python
# coding: utf-8
import os
import sys
import re
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
DOT_OVER_PATTERN_PROBABILITY = 0.3  # Defines how often dots are chosen over pattern on random pattern selection

def show_img(i):
    i.show(command="eog")


def _hex_color_to_tuple(s):
    if not re.search(r'^#?(?:[0-9a-fA-F]{3}){1,2}$', s):
        return (0, 0, 0)
    if len(s) == 3:
        s = "".join(["{}{}".format(c, c) for c in s])
    return tuple(ord(c) for c in s.decode('hex'))

def make_background(size, filename="", dots_prob=None, bg_color="000"):
    """
    Constructs background pattern

    Parameters
    ----------
    size : tuple(int, int)
        Size of the depthmap
    filename : str
        Name of the pattern image, if any. Empty if dot pattern
    dots_prob : float
        Probability of dots appearing. Only makes sense if filename is not set (or equals to 'dots')
    bg_color : str
        hex code for color
    Returns
    -------
    """
    pattern_width = (int)(size[0] / PATTERN_FRACTION)
    # Pattern is a little bit longer than original picture, so everything fits on 3D (eye crossing shrinks the picture horizontally!)
    i = im.new("RGB", (size[0] + pattern_width, size[1]), color=_hex_color_to_tuple(bg_color))
    i_pix = i.load()
    if filename == "R" and random() < DOT_OVER_PATTERN_PROBABILITY:
        filename = "dots"
    # Load from picture
    is_image = False
    if filename != "" and filename != "dots":
        pattern = load_file((get_random("pattern") if filename == "R" else filename))
        if pattern is None:
            #print("Error al cargar '{}'. Generando con puntos aleatorios.".format(filename))
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
                if random() < dots_prob:  # choice([True,False,False,False]):
                    i_pix[c, f] = choice([(255, 0, 0), (255, 255, 0), (200, 0, 255)])

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
        #print("Aborting")
        exit(1)

    # Apply gaussian blur filter
    dm = dm.filter(imflt.GaussianBlur(parsed_args.blur))

    # Redistribute grayscale range
    if parsed_args.text:
        dm = redistribute_grays(dm, parsed_args.forcedepth if parsed_args.forcedepth is not None else 0.5)
    elif parsed_args.forcedepth:
        dm = redistribute_grays(dm, parsed_args.forcedepth)

    # Create base pattern
    bg_image_object, pattern_is_img = make_background(dm.size,
                                                      "" if parsed_args.dots else parsed_args.pattern,
                                                      parsed_args.dot_prob,
                                                      parsed_args.dot_bg_color)

    # Oversample on image-pattern based background (NOT dots, bad results!)
    if pattern_is_img:
        dm = dm.resize(((int)(dm.size[0] * OVERSAMPLE), (int)(dm.size[1] * OVERSAMPLE)))
        bg_image_object = bg_image_object.resize(((int)(bg_image_object.size[0] * OVERSAMPLE), (int)(bg_image_object.size[1] * OVERSAMPLE)))

    pattern_width = (int)(dm.size[0]/float(PATTERN_FRACTION))
    bg_pix = bg_image_object.load()
    dm_pix = dm.load()
    # Empirically obtained. In some place they went from 120px on the shallowest point to 90px (25%)
    depth_factor = pattern_width * SHIFT_RATIO

    if not LEFT_TO_RIGHT:
        # Copy pattern to the middle
        bg_middle_x = bg_image_object.size[0] / 2
        pattern_rect = (0, 0, pattern_width, bg_image_object.size[1])
        pattern_strip = bg_image_object.crop(pattern_rect)
        # bg_image_object = im.new("RGB", (bg_image_object.size[0], bg_image_object.size[1]), color="black")
        bg_image_object.paste(pattern_strip, (bg_middle_x - pattern_width, 0, bg_middle_x, bg_image_object.size[1]))

    # Walk over depthmap
    for y in range(dm.size[1]):
        if LEFT_TO_RIGHT:
            for x in range(pattern_width, bg_image_object.size[0]):
                # From left to right
                this_x = min(max(x - pattern_width, 0), dm.size[0]-1)
                shift = (dm_pix[this_x, y] if parsed_args.wall else (255 - dm_pix[this_x, y])) / 255.0 * depth_factor
                bg_pix[x, y] = bg_pix[x - pattern_width + shift, y]
        else:
            # Walk to the right
            for x in range(bg_middle_x, bg_image_object.size[0]):
                this_gray = dm_pix[min(max(x - pattern_width, 0), dm.size[0]-1), y]
                # Center to right
                this_gray = this_gray if parsed_args.wall else 255 - this_gray
                shift = this_gray / 255.0 * depth_factor
                bg_pix[x, y] = bg_pix[x - pattern_width + shift, y]

            # Walk to the left
            for x in range(bg_middle_x - 1, pattern_width - 1, -1):
                this_gray = dm_pix[x, y]
                # Center to left
                this_gray = this_gray if parsed_args.wall else (255 - this_gray)
                shift = this_gray / 255.0 * depth_factor
                bg_pix[x, y] = bg_pix[x + pattern_width - shift, y]

    if not LEFT_TO_RIGHT:
        bg_image_object.paste(bg_image_object.crop((pattern_width, 0, 2 * pattern_width, bg_image_object.size[1])), pattern_rect)

    # Oversample result and bring back. Smooths everything.
    if pattern_is_img:
        bg_image_object = bg_image_object.resize(((int)(bg_image_object.size[0] / OVERSAMPLE), (int)(bg_image_object.size[1] / OVERSAMPLE)),
                                       im.LANCZOS)  # NEAREST, BILINEAR, BICUBIC, LANCZOS
    return bg_image_object


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


def save_to_file(img_object, output_dir=None):
    """
    Attempts to save the file

    Parameters
    ----------
    img_object: PIL.Image.Image
        The image object to save
    output_dir : The directory where to save the file

    Returns
    -------
    tuple(bool, str)
        State: True if ok
        Additional data: Path to stored image if success, else reason of failure

    """
    file_ext = DEFAULT_OUTPUT_EXTENSION
    # Trying to save with image name format
    if output_dir is None:
        savefolder = SAVEFOLDER
    else:
        savefolder = output_dir
    # Try to create folder, if it doesn't exist already
    if not os.path.exists(savefolder):
        try:
            os.mkdir(savefolder)
        except IOError as e:
            # print "Cannot create file: {}".format(e)
            return False, "Could not create output directory '{}': {}".format(savefolder, e)
    outfile_name = u"{date}{ext}".format(
        date=time.strftime("%Y%m%d-%H%M%S", time.localtime()),
        ext=file_ext
    )
    out_path = os.path.join(savefolder, outfile_name)
    try:
        r = img_object.save(out_path)
        # print "Saved file in {}".format(out_path)
        return True, out_path
    except IOError as e:
        # print("Error trying to save image: {}".format(e))
        return False, "Could not create file '{}': {}".format(out_path, e)


def load_file(name, type=''):
    try:
        i = im.open(name)
        if type != "":
            i = i.convert(type)
    except IOError, msg:
        #print("Picture couln't be loaded '{}': {}".format(name, msg))
        return None
    # Resize if too big
    if max(i.size) > MAX_DIMENSION:
        max_dim = 0 if i.size[0] > i.size[1] else 1
        old_max = i.size[max_dim]
        new_max = MAX_DIMENSION
        factor = new_max/float(old_max)
        #print "Image is big: {}. Resizing by a factor of {}".format(i.size, factor)
        i = i.resize((int(i.size[0]*factor), int(i.size[1]*factor)))
    return i


def obtain_args():
    """
    Retrieves arguments and parses them to a dict.
    """
    def _restricted_unit(x):
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

    def _existent_directory(dirname):
        if not os.path.isdir(dirname):
            raise argparse.ArgumentTypeError("'{}' is not a directory".format(dirname))
        return dirname

    def _valid_color_string(s):
        if not re.search(r'^#?(?:[0-9a-fA-F]{3}){1,2}$', s):
            raise argparse.ArgumentTypeError("'{}' is not a valid hex color".format(s))
        return s

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
    arg_parser.add_argument("--dot-prob", help="Probability of dot apparition", type=_restricted_unit, default=0.4)
    arg_parser.add_argument("--dot-bg-color", help="Base background color for dot pattern", type=_valid_color_string, default="000000")
    arg_parser.add_argument("--blur", "-b", help="Gaussian blur ammount", type=_restricted_blur, default=2)
    arg_parser.add_argument("--forcedepth", help="Force max depth to use", type=_restricted_unit)
    arg_parser.add_argument("--output", "-o", help="Directory where to store the results", type=_existent_directory)
    args = arg_parser.parse_args()
    if args.dot_prob and not args.dots:
        arg_parser.error("--dot-prob only makes sense when --dots is set")
    if args.dot_bg_color and not args.dots:
        arg_parser.error("--dot-bg-color only makes sense when --dots is set")
    # print(args)
    return args


class _HTTPCode:
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


def return_http_response(code, text):
    print json.dumps({
        "code": code,
        "text": text
    })

def main():
    parsed_args = obtain_args()
    i = make_stereogram(parsed_args)
    if not parsed_args.output:
        show_img(i)
        return
    # print "Saving..."
    success, additional_info = save_to_file(i, parsed_args.output)
    if not success:
        return_http_response(_HTTPCode.INTERNAL_SERVER_ERROR, additional_info)
    else:
        return_http_response(_HTTPCode.OK, os.path.basename(additional_info))

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
