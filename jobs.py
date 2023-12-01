import os
from subprocess import Popen as p_open
import cv2

from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.properties import BooleanProperty
from kivy.app import App

from file_management import first_frame, file_date, get_frame, read_vid

class Experiment():
    """Object which represents a micro aspiration experiment.
    There are many events that occur within one experiment.
    The mutable object holds information on the experiment relevant to its analysis.
    Essentially each experiment is a video of an experiment, possibly alongside ion current data"""
    
    def __init__(self, vid_loc):
        # General
        self.name = os.path.basename(vid_loc).split('.')[0]
        # Video file
        self.vid_loc = vid_loc
        self.current_frame = 1
        self.first_frame = first_frame(vid_loc)
        self.cap = read_vid(vid_loc)
        self.num_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Ion current file
        self.ion_loc = ''
        # Grab the dates of creation of the files
        self.vid_date = file_date(self.vid_loc)
        # Event params (used when selecting events)
    
    def add_ion_file(self, file_loc):
        self.ion_loc = file_loc
        self.ion_date = file_date(self.ion_loc)

    def remove_ion_file(self):
        self.ion_loc = ''

    def get_frame(self, prop):
        """prop is proportion through the video"""
        # Calculate the frame number based on the proportion
        target_frame = int((self.num_frames - 1) * prop) + 1
        self.current_frame = target_frame
        return get_frame(self.cap, target_frame - 1)


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
        # Update the visuals
        self.window.update_fields()

    def on_open_btn(self):
        """Called by button on experiment box
        Opens the file/folder associated with the experiment"""
        # Find last slash
        s = str(self.experiment.vid_loc).rfind("\\") + 1
        # E.g. 'C:\Desktop\folder\'
        path = str(self.experiment.vid_loc)[:s]
        # Open that folder in the explorer
        p_open('explorer "' + str(path) + '"')


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
        # For every box
        for exp_box in self.grid_layout.children:
            # If not selected
            if exp_box.experiment != current_experiment:
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