#!/usr/bin/python
"""Main project file, contains everything to generate stereograms."""

import argparse
import json
import os
import re
import codecs
import time
from random import choice, random

# This "PIL" refers to Pillow, the PIL fork. Check https://pillow.readthedocs.io/en/
from PIL import Image as im
from PIL import ImageDraw as imd
from PIL import ImageFilter as imflt
from PIL import ImageFont as imf

from log import Log as log

# Program info
PROGRAM_VERSION = "2.0"

SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpeg", ".bmp", ".eps", ".gif", ".jpg", ".im", ".msp", ".pcx", ".ppm", ".spider", ".tiff", ".webp", ".xbm"]
DEFAULT_DEPTHTEXT_FONT = "freefont/FreeSansBold"
FONT_ROOT = "/usr/share/fonts/truetype"
DEFAULT_OUTPUT_EXTENSION = SUPPORTED_IMAGE_EXTENSIONS[0]
# CONSTANTS
DMFOLDER = "depth_maps"
PATTERNFOLDER = "patterns"
SAVEFOLDER = "saved"

# SETTINGS
MAX_DIMENSION = 1500  # px
PATTERN_FRACTION = 8.0
OVERSAMPLE = 1.8
SHIFT_RATIO = 0.3
LEFT_TO_RIGHT = False  # Defines how the pixels will be shifted (left to right or center to sides)
DOT_OVER_PATTERN_PROBABILITY = 0.3  # Defines how often dots are chosen over pattern on random pattern selection


class Stereogram:
    def __init__(self, args):
        self.args = args
        self.i = None

    def show(self):
        self.i.show(command="eog")

    def generate(self):
        # Load or create stereogram depthmap
        if self.args.text:
            dm_img = self._make_depth_text(self.args.text, self.args.font)
        else:
            dm_img = self._load_file(self.args.depthmap, "L")
        # Apply gaussian blur if needed
        if self.args.blur and self.args.blur != 0:
            dm_img = dm_img.filter(imflt.GaussianBlur(self.args.blur))

        # Redistribute grayscale range (force depth)
        if self.args.text:
            dm_img = self._redistribute_grays(dm_img, self.args.forcedepth if self.args.forcedepth is not None else 0.5)
        elif self.args.forcedepth:
            dm_img = self._redistribute_grays(dm_img, self.args.forcedepth)

        # Create blank canvas
        pattern_width = (int)(dm_img.size[0] / PATTERN_FRACTION)
        canvas_img = im.new(mode="RGB",
                            size=(dm_img.size[0] + pattern_width, dm_img.size[1]),
                            color=(0, 0, 0) if self.args.dot_bg_color is None
                            else self._hex_color_to_tuple(self.args.dot_bg_color))
        # Create pattern
        pattern_strip_img = im.new(mode="RGB",
                                   size=(pattern_width, dm_img.size[1]),
                                   color=(0, 0, 0) if self.args.dot_bg_color is None
                                   else self._hex_color_to_tuple(self.args.dot_bg_color))
        if self.args.pattern:
            # Create from file
            pattern_raw_img = self._load_file(self.args.pattern)
            p_w = pattern_raw_img.size[0]
            p_h = pattern_raw_img.size[1]
            # Resize to strip width
            pattern_raw_img = pattern_raw_img.resize((pattern_width, (int)((pattern_width * 1.0 / p_w) * p_h)),
                                                     im.LANCZOS)
            # Repeat vertically
            region = pattern_raw_img.crop((0, 0, pattern_raw_img.size[0], pattern_raw_img.size[1]))
            y = 0
            while y < pattern_strip_img.size[1]:
                pattern_strip_img.paste(region, (0, y, pattern_raw_img.size[0], y + pattern_raw_img.size[1]))
                y += pattern_raw_img.size[1]

            # Oversample. Smoother results.
            dm_img = dm_img.resize(((int)(dm_img.size[0] * OVERSAMPLE), (int)(dm_img.size[1] * OVERSAMPLE)))
            canvas_img = canvas_img.resize(
                ((int)(canvas_img.size[0] * OVERSAMPLE), (int)(canvas_img.size[1] * OVERSAMPLE)))
            pattern_strip_img = pattern_strip_img.resize(
                ((int)(pattern_strip_img.size[0] * OVERSAMPLE), (int)(pattern_strip_img.size[1] * OVERSAMPLE)))
            pattern_width = pattern_strip_img.size[0]

        else:
            # create random dot pattern
            pixels = pattern_strip_img.load()
            dot_prob = self.args.dot_prob if self.args.dot_prob else 0.4
            if self.args.dot_colors:
                hex_tuples = list()
                for hex_str in self.args.dot_colors.split(','):
                    if re.match(r'.+x\d+', hex_str):
                        # multiplier
                        factor = int(re.sub(r'.*x', '', hex_str))
                        hex_tuples.extend([re.sub(r'x\d+', '', hex_str)] * factor)
                    else:
                        hex_tuples.append(hex_str)
                color_tuples = [self._hex_color_to_tuple(hex) for hex in hex_tuples]
            else:
                color_tuples = [(255, 0, 0), (255, 255, 0), (200, 0, 255)]
            log.d("Colors to use for dots: {}".format(color_tuples))
            for y in range(pattern_strip_img.size[1]):
                for x in range(pattern_width):
                    if random() < dot_prob:
                        pixels[x, y] = choice(color_tuples)

        # Important objects here: dm_img, pattern_strip_img, canvas_img
        # Start stereogram generation
        def shift_pixels(dm_start_x, depthmap_image_object, canvas_image_object, direction):
            """ shifts pixel of image. direction==1 right, -1 left """
            depth_factor = pattern_width * SHIFT_RATIO
            cv_pixels = canvas_image_object.load()
            while 0 <= dm_start_x < dm_img.size[0]:
                for dm_y in range(depthmap_image_object.size[1]):
                    constrained_end = max(0, min(dm_img.size[0] - 1, dm_start_x + direction * pattern_width))
                    for dm_x in range(int(dm_start_x), int(constrained_end), direction):
                        dm_pix = dm_img.getpixel((dm_x, dm_y))
                        px_shift = int(dm_pix / 255.0 * depth_factor * (1 if self.args.wall else -1)) * direction
                        if direction == 1:
                            cv_pixels[dm_x + pattern_width, dm_y] = canvas_img.getpixel((px_shift + dm_x, dm_y))
                        if direction == -1:
                            cv_pixels[dm_x, dm_y] = canvas_img.getpixel((dm_x + pattern_width + px_shift, dm_y))

                dm_start_x += direction * pattern_strip_img.size[0]

        # paste first pattern
        dm_center_x = dm_img.size[0] / 2
        canvas_img.paste(pattern_strip_img, (int(dm_center_x), 0, int(dm_center_x + pattern_width), canvas_img.size[1]))
        if not self.args.wall:
            canvas_img.paste(pattern_strip_img,
                             (int(dm_center_x - pattern_width), 0, int(dm_center_x), canvas_img.size[1]))
        shift_pixels(dm_center_x, dm_img, canvas_img, 1)
        shift_pixels(dm_center_x + pattern_width, dm_img, canvas_img, -1)

        # Bring back from oversample
        if self.args.pattern:
            canvas_img = canvas_img.resize(
                ((int)(canvas_img.size[0] / OVERSAMPLE), (int)(canvas_img.size[1] / OVERSAMPLE)),
                im.LANCZOS)  # NEAREST, BILINEAR, BICUBIC, LANCZOS

        self.i = canvas_img
        return True

    @staticmethod
    def _make_depth_text(text, font):
        canvas_size = (800, 600)  # TODO: Automate
        fontpath = font if os.path.isabs(font) else "{}/{}.ttf".format(FONT_ROOT, font)
        # Create image (grayscale)
        i = im.new('L', canvas_size, "black")
        # Draw text with appropriate gray level
        font_size = 1
        fnt = imf.truetype(fontpath, font_size)
        while fnt.getsize(text)[0] < canvas_size[0] * 0.9 and fnt.getsize(text)[1] < canvas_size[1] * 0.9:
            font_size += 1
            fnt = imf.truetype(fontpath, font_size)
        imd.Draw(i).text(
            ((canvas_size[0] / 2 - fnt.getsize(text)[0] / 2,
              canvas_size[1] / 2 - (fnt.getsize(text)[1] / 2) * 1.2)),
            text, font=fnt,
            fill=((int)(255.0)))
        return i

    @staticmethod
    def _redistribute_grays(dm_image, gray_height):
        """
        For a grayscale depthmap, compresses the gray range to be between 0 and the max gray height

        Parameters
        ----------
        dm_image : PIL.Image.Image
            The open image
        gray_height : float
            Max gray. 0 = black. 1 = white.

        Returns
        -------
        PIL.Image.Image
            Modified image object
        """
        if dm_image.mode != "L":
            dm_image = dm_image.convert("L")
        # Determine min and max gray value
        min_gray = {
            "point": (0, 0),
        }
        min_gray["value"] = dm_image.getpixel(min_gray["point"])
        max_gray = {
            "point": (0, 0),
        }
        max_gray["value"] = dm_image.getpixel(max_gray["point"])

        for x in range(dm_image.size[0]):
            for y in range(dm_image.size[1]):
                this_gray = dm_image.getpixel((x, y))
                if this_gray > dm_image.getpixel(max_gray["point"]):
                    max_gray["point"] = (x, y)
                    max_gray["value"] = this_gray
                if this_gray < dm_image.getpixel(min_gray["point"]):
                    min_gray["point"] = (x, y)
                    min_gray["value"] = this_gray

        # Transform to new scale
        old_min = min_gray["value"]
        old_max = max_gray["value"]
        old_interval = old_max - old_min
        new_min = 0
        new_max = int(255.0 * gray_height)
        new_interval = new_max - new_min

        conv_factor = float(new_interval) / float(old_interval)

        pixels = dm_image.load()
        for x in range(dm_image.size[0]):
            for y in range(dm_image.size[1]):
                pixels[x, y] = int((pixels[x, y] * conv_factor)) + new_min
        return dm_image

    @staticmethod
    def _load_file(file_name, type=''):
        try:
            i = im.open(file_name)
            if type != "":
                i = i.convert(type)
        except IOError as msg:
            log.e("Picture couln't be loaded '{}': {}".format(file_name, msg))
            return None
        # Resize if too big
        if max(i.size) > MAX_DIMENSION:
            max_dim = 0 if i.size[0] > i.size[1] else 1
            old_max = i.size[max_dim]
            new_max = MAX_DIMENSION
            factor = new_max / float(old_max)
            log.d("Image is big: {}. Resizing by a factor of {}".format(i.size, factor))
            i = i.resize((int(i.size[0] * factor), int(i.size[1] * factor)))
        return i

    def save(self):
        file_ext = DEFAULT_OUTPUT_EXTENSION
        # Trying to save with image name format
        if self.args.output is None:
            savefolder = SAVEFOLDER
        else:
            savefolder = self.args.output
        # Try to create folder, if it doesn't exist already
        if not os.path.exists(savefolder):
            try:
                os.mkdir(savefolder)
            except IOError as e:
                log.e("Cannot create file: {}".format(e))
                return False, "Could not create output directory '{}': {}".format(savefolder, e)
        outfile_name = u"{date}{ext}".format(
            date=time.strftime("%Y%m%d-%H%M%S", time.localtime()),
            ext=file_ext
        )
        out_path = os.path.join(savefolder, outfile_name)
        try:
            r = self.i.save(out_path)
            log.d("Saved file in {}".format(out_path))
            return True, out_path
        except IOError as e:
            log.e("Error trying to save image: {}".format(e))
            return False, "Could not create file '{}': {}".format(out_path, e)

    @staticmethod
    def _hex_color_to_tuple(s):
        """
        Parses a hex color string to a RGB triplet.

        Parameters
        ----------
        s: str
            Valid hex color string. Three-chars supported

        Returns
        -------
        tuple: Equivalent RGB triplet

        """
        if not re.search(r'^#?(?:[0-9a-fA-F]{3}){1,2}$', s):
            return (0, 0, 0)
        if len(s) == 3:
            s = "".join(["{}{}".format(c, c) for c in s])
        return tuple(int(c) for c in codecs.decode(s, 'hex'))  # s.decode('hex'))



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

    def _valid_colors_list(s):
        colors = s.strip().split(",")
        validated_colors = [_valid_color_string(re.sub(r'x\d+', '', color_string)) for color_string in colors]
        return s

    arg_parser = argparse.ArgumentParser(description="Stereogramaxo: An autostereogram generator")
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
    dotprops_arg_group = arg_parser.add_argument_group()
    dotprops_arg_group.add_argument("--dot-prob", help="Dot apparition probability", type=_restricted_unit)
    dotprops_arg_group.add_argument("--dot-bg-color", help="Background color", type=_valid_color_string)
    dotprops_arg_group.add_argument("--dot-colors",
                                    help="Comma separated list of hex colors. Supports multipliers, "
                                         "i.e.: fff,ff0000x3 results in 3 times more ff0000 than fff",
                                    type=_valid_colors_list)
    arg_parser.add_argument("--blur", "-b", help="Gaussian blur ammount", type=_restricted_blur)
    arg_parser.add_argument("--forcedepth", help="Force max depth to use", type=_restricted_unit)
    arg_parser.add_argument("--output", "-o", help="Directory where to store the results", type=_existent_directory)
    arg_parser.add_argument("--font", "-f",
                            help="Truetype font file to use. If relative path, font root is '{}'"
                            .format(FONT_ROOT),
                            default=DEFAULT_DEPTHTEXT_FONT)
    args = arg_parser.parse_args()
    if args.dot_prob and not args.dots:
        arg_parser.error("--dot-prob only makes sense when --dots is set")
    if args.dot_bg_color and not args.dots:
        arg_parser.error("--dot-bg-color only makes sense when --dots is set")
    if args.dot_colors and not args.dots:
        arg_parser.error("--dot-colors only makes sense when --dots is set")
    if not args.blur:
        args.blur = 2 if args.depthmap else 8
    return args


class _HTTPCode:
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


def return_http_response(code, text):
    print(json.dumps({
        "code": code,
        "text": text
    }))


def main():
    parsed_args = obtain_args()
    t0 = time.time()
    s = Stereogram(parsed_args)
    success = s.generate()
    if not success:
        log.e("Something went wrong")
        return
    if not parsed_args.output:
        log.i("Process finished successfully after {0:.2f}s".format(time.time() - t0))
        log.i("No output file specified. Showing in temporary preview")
        s.show()
        return
    success, additional_info = s.save()
    if not success:
        log.e("Process finished with errors: '{}'".format(additional_info))
        return_http_response(_HTTPCode.INTERNAL_SERVER_ERROR, additional_info)
    else:
        log.i("Process finished successfully after {0:.2f}.s".format(time.time() - t0))
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

# TODO: Provide option to match pattern height
# TODO: Put generation options as image metadata
# TODO: OOP