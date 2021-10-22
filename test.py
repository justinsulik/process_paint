# example script for processing data output by a jspsych experiment
# containing a jspsych-paint-d3.js plugin

import json, numpy as np, pandas as pd, os, re
from PIL import Image, ImageOps
from process_jspaint_data import process_paint

# file_in should point to the json file containing the experiment data
file_in = "test_data/test_paint_task.json"
# this should reflect the size of the sketch in the experiment
size = 480

# Set up masks for body outlines
## Whole body
whole_body_mask = Image.open("masks/body_mask_double.png").resize((size,size))

# Set up masks for aggregating by zones.
parts = []
for file in os.listdir("masks"):
    if 'body_' in file and 'mask' not in file and 'image' not in file:
        part_found = re.search('([a-zA-Z]*)\.png', file)
        if part_found:
           part = part_found.group(1)
           parts.append(part)
## first, create a dict for the mask images to go into
aggregate_masks = {}
for part in parts:
    # load the individual masks and convergt to greyscale
    part_img = Image.open('masks/body_{}.png'.format(part)).resize((int(size/2),size)).convert('RGB')
    part_grey = ImageOps.grayscale(part_img)
    # convert to numpy matrix and change zeroes to NaN
    part_mat = np.array(part_grey).astype('float')
    part_mat[part_mat == 0] = np.nan
    part_mat[part_mat == 255] = 1
    aggregate_masks[part] = part_mat

# for storing the aggregate data
data_dict = {}

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
                # or file-system data (e.g., path to a folder).
                # But as there is no such data in the test file, I'm just using participant_id as the unique name
                aggregate_data = process_paint(strokes_json, participant_id, whole_body_mask, aggregate_masks=aggregate_masks)
                # store the aggregate data across participants
                data_dict[participant_id] = aggregate_data
                # do something sensible with the aggregate_data for each image, e.g. add to csv

# Transform the data into a dataframe
data_df = pd.DataFrame.from_dict(data_dict, orient="index")
# Save it
data_df.to_csv("data_out/data.csv")
