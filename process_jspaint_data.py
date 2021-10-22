# Process paint data from a jspsych-paint-d3.js plugin.
# An external script (see example.py) should process the overall experiment json data,
# and when it sees a 'paint' trial, extract the strokes parameter,
# passing it to the function process_paint below.

# drawSvg needs Cairo installed separately:
# https://pypi.org/project/drawSvg/

# "strokes" in what follows is the data for a single drawing stroke, like a stroke of the pen
# (i.e., from mouse down to mouse up) in the jspsych-paint-d3.js plugin.
# It is an object that has properties:
# color - hex color of the stroke
# size - width of the drawing nib
# width - width of the drawing canvas
# height - height of the drawing canvas
# stroke - list of [x, y] positions

import json
import drawSvg as draw
import numpy as np
from PIL import Image, ImageOps

def process_paint(strokes_json, file_id,
    whole_mask, aggregate_masks = None,
    out_width = 480, out_height = 480,
    render_jpg=True, flip_y=True):
    # strokes_json: the value of the strokes parameter from a jspsych-paint-d3.js plugin (as json)
    # file_id: unique identifier for this painting trial
    # out_width/height: int size of file output
    # save_png: if true, save a png file from the svg data
    # render_jpg: if true, render+save a jpg file
    # aggregate_masks: optionally, a dict with (string) body part names as keys masking images as values - only use if render_jpg == True
    # flip_y: it seems the gorilla data is flipped about the y-axis. If True, the output will be flipped horizontally

    # this function calls subsequent functions to:
    # convert this json string into a dict
    # render this raw stroke data as a png (if save_png is true)
    # and convert it to a jpg (if render_jpg is true)
    # and aggregate by body part (if a mask file is provided in masks)

    strokes = json.loads(strokes_json)

    # all strokes should be on the same size canvas, so just get the canvas width, height from the first stroke
    if len(strokes) > 0:
        width = strokes[0]['width']
        height = strokes[0]['height']
        # check if the image is front+back (in which case it will be square; otherwise height=width*2)
        double_wide = True if height == width else False
        render_png(strokes, file_id, width, height, out_width, out_height, flip_y)
        if render_jpg:
            image = convert_jpg(file_id, out_width, out_height, whole_mask)
            if aggregate_masks:
                aggregate_data = aggregate_zones(image, aggregate_masks, double_wide, width, height)
                return aggregate_data
    else:
        print("There no paint data for ID {}".format(file_id))

def aggregate_zones(image, masks, double_wide, width, height):
    # we really only need the blue channel here
    image_mat = np.array(image)[:,:,2]
    aggregate_data = {}
    if double_wide:
        # if it is double_wide, separate image into front and back halves,
        halfway = int(width/2)
        sides = {'front': image_mat[:,:halfway], 'back': image_mat[:,halfway:]}
        for side in sides:
            for part in masks:
                zone_data = stamp_mask(sides[side], masks[part])
                aggregate_data['{}_{}'.format(part,side)] = zone_data
    else:
        for part in masks:
            zone_data = stamp_mask(image_mat, masks[part])
            aggregate_data[part] = zone_data
    return aggregate_data

def stamp_mask(image, mask):
    # multiply image * mask
    stamped = np.multiply(image, mask)
    # calculate average
    average = round(np.nanmean(stamped)/255, 2)
    return average

def convert_jpg(file_id, out_width, out_height, whole_mask):
    raw = Image.open("images_out/png/{}.png".format(file_id))
    raw.paste(whole_mask, (0,0), whole_mask) #second 'mask' needed to use the transparency
    rgb_masked = raw.convert('RGB')
    rgb_masked.save("images_out/jpg/{}.jpg".format(file_id), quality=95, subsampling=0)
    return rgb_masked

def render_png(strokes, file_id, width, height, out_width, out_height, flip_y):
    d = draw.Drawing(width, height, displayInline=False)
    # for gaps in the drawing, can fill in the following be fill=NA?
    d.append(draw.Rectangle(0,0,width,height, fill='#808080'))
    for brushstroke in strokes:
        if flip_y:
            stroke_path = [[point[0], height-point[1]] for point in brushstroke['stroke']]
        else:
            strok_path = brushstroke['stroke']
        points = [item for sublist in stroke_path for item in sublist]
        d.append(draw.Lines(*points,
            close=False,
            fill=None,
            fill_opacity=0,
            stroke=brushstroke['color'],
            stroke_width=brushstroke['size'],
            stroke_linejoin='round',
            stroke_linecap='round'))
    d.setRenderSize(out_width, out_height)
    d.savePng('images_out/png/{}.png'.format(file_id))
