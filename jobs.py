import os
from datetime import datetime

def file_date(file_loc):
    if os.path.exists(file_loc):
        date = datetime.fromtimestamp(os.path.getctime(file_loc)).strftime(
            "%d/%m/%Y"
        )
    elif file_loc == '':
        date = "No file selected."
    else:
        date = "File not found."
    return date

class Experiment():
    """Object which represents a replicate from a micro aspiration experiment.
    There are many events that occur within one experiment.
    The mutable object holds information on the experiment relevant to its analysis."""
    
    def __init__(self, vid_loc):
        # General
        self.name = ''
        self.is_selected = True
        # Video file
        self.vid_loc = ''
        self.vid_dims = ()
        self.vid_num_frames = 0
        self.first_frame = ''
        # Ion current file
        self.ioncur_loc = ''
        self.ioncur_dims = ()
        self.ioncur_num_frames = 0
        self.first_frame = ''
        # Grab the dates of creation of the files
        self.vid_date = file_date(self.vid_loc)
        self.ioncur_date = file_date(self.ioncur_loc)

        

class Event():
    """Object which represents a replicate from a micro aspiration event.
    There are many events that occur within one experiment.
    The mutable object holds information on the event relevant to its analysis."""
    
    def __init__(self, vid_loc):
        # General
        self.name = ''
        self.experiment = None
        self.is_selected = True
        # Video file
        self.vid_loc = ''
        self.vid_dims = ()
        self.vid_num_frames = 0
        self.first_frame = ''
        # Ion current file
        self.ioncur_loc = ''
        self.ioncur_dims = ()
        self.ioncur_num_frames = 0
        self.first_frame = ''
