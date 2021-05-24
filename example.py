# example script for processing data output by a jspsych experiment
# containing a jspsych-paint-d3.js plugin

import json
from PIL import Image, ImageOps
from process_jspaint_data import process_paint

# file_in should point to the json file containing the experiment data
file_in = "test_data/test_paint_task.json"
size = 480

# Set up masks for body outlines
## Whole body
whole_body_mask = Image.open("masks/body_mask_double.png").resize((size,size))
## Half body
half_body = Image.open("masks/body_half_trim.png").resize((int(size/2),size))
half_body_mask = Image.new('L', (size, size))
half_body_mask.paste(half_body, (0,0))
half_body_mask.paste(half_body, (int(size/2),0))

# Set up masks for aggregating by zones. In this example, I'm just doing 2: hands and shoulders, with a front and back version of each
parts = ['hands', 'shoulders']
## first, create a dict for the mask images to go into
aggregate_masks = {}
# for part in parts:
#     # load the individual masts
#     part_image = Image.open('masks/aggregate_{}.png'.format(part)).resize((288,480))
#     # create a mask
#     mask = Image.new('L', (part_image.width*2, part_image.height))
#     # create one copy for the front
#     front = mask.copy()
#     front.paste(part_image, (0,0))
#     aggregate_masks['{}_front'.format(part)] = front
#     # create another copy for the back
#     back = mask.copy()
#     back.paste(part_image, (part_image.width, 0))
#     aggregate_masks['{}_back'.format(part)] = back

with open(file_in, "r") as data_file:
    for data_json in data_file:
        data = json.loads(data_json)
        for trial in data:
            if trial['trial_type'] == 'paint':
                participant_id = trial['participant_id']
                strokes_json = trial['strokes']
                # create a unique name for this picture
                # this can incorporate trial-level data (e.g., what the picture is)
                # participant-level data (e.g., their id/demographics)
                # study-level data
                # or file-system data (e.g., path to a folder)
                # as there is no such data in the test file, I'm just using participant_id as the unique name
                aggregate_data = process_paint(strokes_json, participant_id, whole_body_mask)
                # do something sensible with the aggregate_data for each image, e.g. add to csv
