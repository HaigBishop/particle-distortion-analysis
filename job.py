
class PDAjob():
    """Object which represents a replicate from a micro aspiration experiment.
    The mutable object holds information on the job relevant to its analysis."""
    
    def __init__(self):
        # Job
        self.name = ''
        self.is_selected = True
        # Video file
        self.vid_loc = ''
        self.vid_dims = ()
        self.vid_num_frames = 0
        self.first_frame = ''
        # Tracking
        self.tip_locs = []
        self.side_locs = []
