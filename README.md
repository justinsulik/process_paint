
Two python scripts for processing data from a custom jsPsych plugin, where participants paint on a body silhouette to indicate how comfortable/uncomfortable it would be if someone touched them there. 

# example.py

Processes the jsPsych json output, including setting up any masks (for the body silhouettes) needed to render the image

# process_jspaint_data.py

takes the jsPsych plugin out put, and renders a png of the raw brush strokes, as well as a jpg with the body silhouette imposed as a mask. 
