import os

from file_management import first_frame, file_date

class Experiment():
    """Object which represents a replicate from a micro aspiration experiment.
    There are many events that occur within one experiment.
    The mutable object holds information on the experiment relevant to its analysis."""
    
    def __init__(self, vid_loc):
        # General
        self.name = os.path.basename(vid_loc).split('.')[0]
        # Video file
        self.vid_loc = vid_loc
        self.first_frame = first_frame(vid_loc)
        # Ion current file
        self.ion_loc = ''
        # Grab the dates of creation of the files
        self.vid_date = file_date(self.vid_loc)
    
    def add_ion_file(self, file_loc):
        self.ion_loc = file_loc
        self.ion_date = file_date(self.ion_loc)

    def remove_ion_file(self):
        self.ion_loc = ''

        

class Event():
    """Object which represents a replicate from a micro aspiration event.
    There are many events that occur within one experiment.
    The mutable object holds information on the event relevant to its analysis."""
    
    def __init__(self, vid_loc):
        # General
        self.name = ''
        self.experiment = None
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
