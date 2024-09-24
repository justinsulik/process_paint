# example script for processing data output by a jspsych experiment
# containing a jspsych-paint-d3.js plugin

import json, numpy as np, pandas as pd, os, re
from PIL import Image, ImageOps
from process_jspaint_data import process_paint
from collections import defaultdict

# data_in should point to the directory containing the json files; images_out is folder where images should be stored
data_in = "data_in_covid"
data_out = "data_out_covid"
images_out = "images_out_covid"

# this should reflect the size of the sketch in the experiment...
# in phase1 (whole body) it was 480x480
# but in phase 4 (half body) the single-side mask was 368*613, so if width was 480 then height was 480*613/(2*368) = 399.78
sketch_sizes = {
    'body': {'width': 480, 'height': 480},
    'bodyhalf': {'width': 480, 'height': 400},
    'bodyhalf_single': {'width': 480, 'height': 480}
}

# Set up masks for body outlines
whole_body_mask = Image.open("masks/body/mask_double.png").resize((sketch_sizes['body']['width'], sketch_sizes['body']['height']))
half_body_mask = Image.open("masks/bodyhalf/mask.png").resize((int(sketch_sizes['bodyhalf']['width']/2), sketch_sizes['bodyhalf']['height']))
half_body_mask_single = Image.open("masks/bodyhalf_single/mask.png").resize((sketch_sizes['bodyhalf_single']['width'], sketch_sizes['bodyhalf_single']['height']))

# Set up masks for aggregating by zones.
# Each of the above (whole body / half body) could have a separate set of masks
parts = {}
for maskset in os.listdir("masks/"):
    if '.' not in maskset:
        parts[maskset] = []
        for file in os.listdir("masks/" + maskset + "/"):
            if 'body_' in file and 'mask' not in file and 'map' not in file:
                part_found = re.search('([a-zA-Z]*)\.png', file)
                if part_found:
                    part = part_found.group(1)
                    parts[maskset].append(part)

# first, create a dict for the mask images to go into
bodypart_masks = {}
for maskset in parts:
    bodypart_masks[maskset] = defaultdict(dict)
    for part in parts[maskset]:
        if maskset == 'bodyhalf_single':
            mask_width = int(sketch_sizes[maskset]['width'])
        else:
            mask_width = int(sketch_sizes[maskset]['width']/2)
        mask_height = sketch_sizes[maskset]['height']
        # load the individual masks and convert to greyscale        
        part_img = Image.open('masks/{}/body_{}.png'.format(maskset, part)).resize((mask_width, mask_height)).convert('RGB')
        part_grey = ImageOps.grayscale(part_img)
        # convert to numpy matrix and change zeroes to NaN
        part_mat = np.array(part_grey).astype('float')
        ## The full and half masks seem to be opposites (in terms of mask v background)
        if maskset == 'body':
            part_mat[part_mat == 0] = np.nan
            part_mat[part_mat == 255] = 1
        else:
            part_mat[part_mat == 0] = 1
            part_mat[part_mat == 255] = np.nan
        bodypart_masks[maskset][part] = part_mat


# iterate over json files
for file_in in os.listdir(data_in):
    if 'json' in file_in:
        if re.search('[0-9].json', file_in):
            # for storing the aggregate data
            data_dict = {}

            phase = re.search('([0-9]).json', file_in).group(1)
            if phase == '2':
                image_out_path = f"{images_out}/phase{phase}/"
                if not os.path.exists(image_out_path):
                    os.makedirs(image_out_path)
                if not os.path.exists(image_out_path+'png/'):
                    os.makedirs(image_out_path+'png/')
                if not os.path.exists(image_out_path+'jpg/'):
                    os.makedirs(image_out_path+'jpg/')
                if phase == '1':
                    mask = whole_body_mask
                    aggregate_masks = bodypart_masks['body']
                    image_size = sketch_sizes['body']
                    double_mask = False
                    double_aggr = True
                elif phase == '2':
                    mask = half_body_mask_single
                    aggregate_masks = bodypart_masks['bodyhalf_single']
                    image_size = sketch_sizes['bodyhalf_single']
                    double_mask = False
                    double_aggr = False
                else:
                    mask = half_body_mask
                    aggregate_masks = bodypart_masks['bodyhalf']
                    image_size = sketch_sizes['bodyhalf']
                    double_mask = True
                    double_aggr = True
                with open(f"{data_in}/{file_in}", "r") as data_file:
                    data = json.load(data_file)
                    for trial in data:
                        if trial['trial_type'] == 'paint':
                            participant_id = trial['participant']
                            relationship = trial['relationship']
                            strokes_json = trial['strokes']
                            # create a unique name for this picture
                            # this can incorporate trial-level data (e.g., what the picture is)
                            # participant-level data (e.g., their id/demographics)
                            # study-level data
                            # or file-system data (e.g., path to a folder).
                            # But as there is no such data in the test file, I'm just using participant_id as the unique name
                            image_id = '{}_{}'.format(participant_id, relationship)
                            aggregate_data = process_paint(strokes_json, image_id, mask, 
                                                            out_width = image_size['width'], out_height = image_size['height'], 
                                                            aggregate_masks=aggregate_masks, 
                                                            double_mask = double_mask, 
                                                            double_aggr=double_aggr,
                                                            save_image_path=image_out_path)
        
                            # store the aggregate data across participants
                            data_dict[(participant_id, relationship)] = aggregate_data
                        
                # Transform the data into a dataframe
                if len(data_dict) > 0:
                    
                    data_df = pd.DataFrame.from_dict(data_dict, orient="index").reset_index(names=['participant', 'relationship'])
                    # Save it
                    data_df.to_csv(f"{data_out}/phase{phase}_topology_aggr.csv", index=False)
