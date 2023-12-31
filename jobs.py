"""
Module:  All classes related to Experiments and Events
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.properties import BooleanProperty
from kivy.app import App

# Import modules
import os
from subprocess import Popen as p_open
from scipy.signal import decimate

# Import local modules
from file_management import *

# Desired size to downsample signal data
# raw data is not discarded, this is only used for display
# e.g. 250,000 yeilds new data in the range of 250,000-500,000
DESIRED_SIGNAL_SIZE = 250000


class Experiment():
    """Object which represents a micro aspiration experiment.
    There are many events that occur within one experiment.
    The mutable object holds information on the experiment relevant to its analysis.
    Essentially each experiment is a video of an experiment, possibly alongside ion current data"""
    
    def __init__(self, vid_loc):
        # General
        self.name, self.file_extension = os.path.splitext(os.path.basename(vid_loc))
        self.directory, _ = os.path.split(vid_loc)
        # Video file
        self.vid_loc = vid_loc
        self.current_frame = 1
        self.cap = read_vid(vid_loc)
        self.first_frame = get_frame(self.cap, 1)
        self.shape = self.first_frame.shape
        self.num_frames = count_frames(vid_loc)
        # Grab the dates of creation of the files
        self.vid_date = file_date(self.vid_loc)
        
        # Ion current file
        self.ion_loc = ''
        self.ion_date = None
        # Ion current data
        self.ioncurr_sig, self.strobe_sig, self.ioncurr_len, self.strobe_len = None, None, None, None
        self.downsampled_ioncurr_sig, self.decimation_factor = None, None
        # Ion current time metadata
        self.t_step, self.sample_freq, self.loop_factor, self.time_scale = None, None, None, None
        # Shift and zoom to line up video and current data
        self.ion_frame_range = None

        # Event params (used when selecting events)
        self.event_start_frame = None
        self.event_ranges = []

        # Maximum zoom in zoom range
        self.zoom_max = 0.01
    
    def add_ion_file(self, file_loc):
        """Reads a TDMS file and holds information in this object.
        - We can assume that the given file is readable as an ion current file"""
        # Save file loc and date
        self.ion_loc = file_loc
        self.ion_date = file_date(self.ion_loc)
        # Read the file and extract data
        self.ioncurr_sig, self.strobe_sig, self.ioncurr_len, self.strobe_len, self.t_step, self.sample_freq, self.loop_factor, self.time_scale = read_tdms(file_loc)
        # Filter the data
        self.ioncurr_sig = fft_and_filter(self.ioncurr_sig, self.sample_freq)
        # Normalise and smooth signal
        self.ioncurr_sig = normalise_and_smooth_sig(self.ioncurr_sig, self.sample_freq)
        # Downsample if needed!
        self.decimation_factor = 1
        self.downsampled_ioncurr_sig = self.ioncurr_sig
        # While too big
        while len(self.downsampled_ioncurr_sig) > DESIRED_SIGNAL_SIZE * 1.99:
            # Make 2x smaller
            self.downsampled_ioncurr_sig = decimate(self.downsampled_ioncurr_sig, 2)
            self.decimation_factor *= 2
        # Set maximum zoom in zoom range according to the length of the signal
        self.zoom_max = min(max(0.01, 5000 / self.ioncurr_len), 1.0)
        # Set shift and zoom to first and last frames
        self.ion_frame_range = (1, self.num_frames)
        
    def remove_ion_file(self):
        """Resets the ion current related data."""
        # Ion current file
        self.ion_loc = ''
        self.ion_date = None
        # Ion current data
        self.ioncurr_sig, self.strobe_sig, self.ioncurr_len, self.strobe_len = None, None, None, None
        self.downsampled_ioncurr_sig, self.decimation_factor = None, None
        # Ion current time metadata
        self.t_step, self.sample_freq, self.loop_factor, self.time_scale = None, None, None, None
        # Shift and zoom to line up video and current data
        self.ion_frame_range = None

    def get_frame(self, frame_num):
        """yeah"""
        frame_num = self.num_frames if frame_num > self.num_frames else frame_num
        frame = get_frame(self.cap, frame_num - 1)
        # If didn't work
        if frame is None:
            # Return a blank image
            frame = np.ones(self.shape, dtype=np.uint8) * 255
        return frame




class ExperimentBox(Button):
    """experiment widget on the ExperimentList scrollview widget"""
    is_selected = BooleanProperty(False)

    def __init__(self, experiment, window, **kwargs):
        """init method for experiment boxes on a experiment list scrollview"""
        self.experiment = experiment
        self.window = window
        # Save app as an attribute
        self.app = App.get_running_app()
        # Call Button init method
        super().__init__(**kwargs)

    def on_press(self):
        """called when the experiment box is pressed
        - sets this experiment to be current
        - enables layouts
        - updates visuals
        - scrolls textboxes back to the start"""
        # This is now the current experiment
        self.app.select_experiment(self.experiment)

    def on_open_btn(self):
        """Called by button on experiment box
        Opens the file/folder associated with the experiment"""
        # Open that folder in the explorer
        p_open('explorer "' + str(self.experiment.directory) + '"')


class ExperimentList(ScrollView):
    """scrolling widget which holds experiments"""

    def __init__(self, **kwargs):
        """init method for the scrolling widget in IE1"""
        # Save app as an attribute
        self.app = App.get_running_app()
        # Call ScrollView init method
        super(ExperimentList, self).__init__(**kwargs)

    def clear_list(self, boxes_only=False):
        # While there are still boxs
        while len(self.grid_layout.children) != 0:
            # Get the first box
            box = self.grid_layout.children[0]
            # Remove current frame
            box.experiment.current_frame = 1
            # Remove the first box
            self.grid_layout.remove_widget(box)
        # If not only clearing boxes
        if not boxes_only:
            # clear experiment objects
            self.app.experiments.clear()
        # Update visual stuff
        self.window.update_fields()

    def on_x_btn(self, box, screen_id):
        """called when an x button on a box is pressed
        - disables the layouts because there is nothing selected now
        - removes the experiments
        - updates visuals"""
        # Remove that experiment
        self.grid_layout.remove_widget(box)
        # If on first screen after main
        if screen_id in ["IE1"]:
            # Remove the experiment
            self.app.remove_experiment(box.experiment)
        else:
            # Just deselect the experiment
            self.app.deselect_all_experiments()
        # Update visual stuff
        self.window.update_fields()

    def on_current_experiment(self, instance, current_experiment):
        self.update_is_selected()

    def update_is_selected(self):
        # For every box
        for exp_box in self.grid_layout.children:
            # If not selected
            if exp_box.experiment != self.app.current_experiment:
                exp_box.is_selected = False
            # If selected
            else:
                exp_box.is_selected = True


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


class EventBox(Button):
    """event widget on the EventList scrollview widget"""
    is_selected = BooleanProperty(False)

    def __init__(self, event, window, **kwargs):
        """init method for event boxes on a event list scrollview"""
        self.event = event
        self.window = window
        # Save app as an attribute
        self.app = App.get_running_app()
        # Call Button init method
        super().__init__(**kwargs)
        

class EventList(ScrollView):
    """scrolling widget which holds events"""

    def __init__(self, **kwargs):
        """init method for the scrolling widget"""
        # Save app as an attribute
        self.app = App.get_running_app()
        # Call ScrollView init method
        super(EventList, self).__init__(**kwargs)
