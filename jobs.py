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
import numpy as np
import cv2

# Import local modules
from file_management import read_vid, get_frame, count_frames, file_date, fft_and_filter, normalise_and_smooth_sig, align_sig_to_frames, read_tdms
from tracking import detect_start

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

        # A list of the event objects (only used after leaving IE3)
        self.events = []

        # Maximum zoom in zoom range
        self.zoom_max = 0.01

        # A JSON file attached to this exp which describes it and its event
        self.json_file_loc = None
    
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

    def add_event(self, event):
        """Adds an event"""
        self.events.append(event)

    def clear_events(self):
        """Clears all events"""
        self.events = []
    
    def make_events(self, use_ion):
        """Simply makes event objects for all events of this experiment using the self.event_ranges"""
        # Make a list to hold all events
        events = []
        # If we have any events selected
        if len(self.event_ranges) > 0:
            # If using ion
            if use_ion:
                # Align/zoom signal to the video frames
                aligned_signal = align_sig_to_frames(self.ioncurr_sig, self.num_frames, self.ion_frame_range)
            # For every event
            i = 1
            for first_frame, last_frame in self.event_ranges:
                # If using ion
                if use_ion:
                    # Grab ion current data between first_frame and last_frame
                    start_i = int(((first_frame - 1) / self.num_frames) * len(aligned_signal))
                    end_i = int(((last_frame) / self.num_frames) * len(aligned_signal) + 1)
                    ion_data = aligned_signal[start_i : end_i]
                    # As a python list with Nones not NaNs
                    ion_data = [None if np.isnan(x) else x for x in ion_data.tolist()]
                # If not using ion
                else:
                    ion_data = None
                # Construct an event
                event = Event(i, self, first_frame, last_frame, ion_data)
                # Add to the list
                events.append(event)
                # next ID
                i += 1
        return events


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
    
    def __init__(self, id, experiment, first_frame_num, last_frame_num, ion_data):
        # General
        self.id = id
        self.experiment = experiment
        self.name = experiment.name + "_evt_" + str(id)
        # Video stuff
        self.first_frame_num = first_frame_num
        self.last_frame_num = last_frame_num
        self.num_frames = last_frame_num - first_frame_num + 1
        self.first_frame = get_frame(self.experiment.cap, first_frame_num)
       
        # Ion current file
        self.ion_data = ion_data

        # Start point features (from prediction/user input)
        self.particle_pos = None
        self.particle_radius = None
        self.pipette_angle = None
        self.left_bottom_x = None
        self.right_bottom_x = None

    def predict_start(self):
        """Predict the position, angle, etc of the start point.
        Then, update those values so they can be displayed... or exported etc."""
        # Run the first frame through the algorithm
        particle_pos, particle_radius, pipette_angle, left_bottom_x, right_bottom_x = detect_start(self.first_frame, display=False)
        # Update the values
        self.particle_pos = particle_pos
        self.particle_radius = particle_radius
        self.pipette_angle = pipette_angle
        self.left_bottom_x = left_bottom_x
        self.right_bottom_x = right_bottom_x

    def drawn_first_frame(self, zoomed):
        """Take the first frame, draw the position, angle, etc. Return it.
        - the particle is simply a circle with position and radius given
        - the pipette consists of two lines (angle given) and end at their bottom_x value."""
        # Draw the particle
        frame = self.first_frame.copy()
        if self.particle_pos is not None and self.particle_radius is not None:
            cv2.circle(frame, (int(self.particle_pos[0]), int(self.particle_pos[1])), int(self.particle_radius), (0, 0, 255), 1)
        # Draw the pipette
        if self.pipette_angle is not None and self.left_bottom_x is not None and self.right_bottom_x is not None:
            # Get the height of the image
            height = self.first_frame.shape[0]
            # Draw 2 lines representing the pipette sides
            line_start = (int(self.left_bottom_x), int(0))
            line_end = (int(self.left_bottom_x + self.pipette_angle * height), int(height))
            cv2.line(frame, line_start, line_end, (0, 0, 255), 1)
            line_start = (int(self.right_bottom_x), int(0))
            line_end = (int(self.right_bottom_x + self.pipette_angle * height), int(height))
            cv2.line(frame, line_start, line_end, (0, 0, 255), 1)
        # Zoom by cropping the image centred on the circle
        if zoomed:
            # Get the centre of the circle
            centre_x = int(self.particle_pos[0])
            centre_y = int(self.particle_pos[1])
            # Get the radius of the circle
            radius = int(self.particle_radius)
            # Get the size of the image
            height, width = self.first_frame.shape[:2]
            # Get the new size of the image and maintain aspect ratio
            if height > width:
                new_height = int(radius * 6 * (height / width))
                new_width = int(radius * 6)
            else:
                new_height = int(radius * 6)
                new_width = int(radius * 6 * (width / height))
            # Get the new top left corner of the image
            top_left_x = centre_x - int(new_width / 2)
            top_left_y = centre_y - int(new_height / 2)
            # Get the new bottom right corner of the image
            bottom_right_x = centre_x + int(new_width / 2)
            bottom_right_y = centre_y + int(new_height / 2)
            # Crop the image
            frame = frame[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
        # Return the frame
        return frame
    
    def zoom_in_pipette(self):
        """Simply moves the pipette positions closer together"""
        # If they are more than 10 pixels apart
        if self.right_bottom_x - self.left_bottom_x > 10:
            # Move the pipette closer together
            self.left_bottom_x = self.left_bottom_x + 1
            self.right_bottom_x = self.right_bottom_x - 1
    
    def zoom_out_pipette(self):
        """Simply moves the pipette positions further apart"""
        # If they are less than 25% the width of the frame apart
        if self.right_bottom_x - self.left_bottom_x < self.first_frame.shape[1] / 4:
            self.left_bottom_x = self.left_bottom_x - 1
            self.right_bottom_x = self.right_bottom_x + 1
    
    def move_left_pipette(self):
        """Tilts the pipette left"""
        # If angle is below 0.2
        if self.pipette_angle < 0.2:
            # Move the pipette left
            self.pipette_angle = self.pipette_angle + 0.005
    
    def move_right_pipette(self):
        """Tilts the pipette right"""
        # If angle is above -0.2
        if self.pipette_angle > -0.2:
            # Move the pipette right
            self.pipette_angle = self.pipette_angle - 0.005

    def move_up_circle(self):
        """Moves the circle up"""
        # If particle_pos is within 10 pixels of the edge
        if self.particle_pos[1] < self.first_frame.shape[0] - 10:
            # Move the circle up
            x, y = self.particle_pos
            self.particle_pos = (x, y - 1)
    
    def move_down_circle(self):
        """Moves the circle down"""
        # If particle_pos is within 10 pixels of the edge
        if self.particle_pos[1] > 10:
            x, y = self.particle_pos
            self.particle_pos = (x, y + 1)

    def move_left_circle(self):
        """Moves the circle left"""
        # If particle_pos is within 10 pixels of the edge
        if self.particle_pos[0] > 10:
            # Move the circle left
            x, y = self.particle_pos
            self.particle_pos = (x - 1, y)
    
    def move_right_circle(self):
        """Moves the circle right"""
        # If particle_pos is within 10 pixels of the edge
        if self.particle_pos[0] < self.first_frame.shape[1] - 10:
            # Move the circle right
            x, y = self.particle_pos
            self.particle_pos = (x + 1, y)

    def zoom_in_circle(self):
        """Zoom in on the circle"""
        # If radius is below 1/4 image size
        if self.particle_radius < self.first_frame.shape[1] / 4:
            # Zoom out on the circle
            self.particle_radius = self.particle_radius + 1   

    def zoom_out_circle(self):
        """Zoom out on the circle"""
        # If radius is above 5
        if self.particle_radius > 5:
            # Zoom out on the circle
            self.particle_radius = self.particle_radius - 1
         

    def update_pos(self, pos):
        """Takes a position (in terms of the original image) and updates the particle_pos
        Assumes the position is valid"""
        self.particle_pos = pos
        


class EventBox(Button):
    """event widget on the EventList scrollview widget"""
    is_selected = BooleanProperty(False)

    def __init__(self, event, window, **kwargs):
        """init method for event boxes on a event list scrollview"""
        self.event = event
        self.experiment = event.experiment
        self.window = window
        # Save app as an attribute
        self.app = App.get_running_app()
        # Call Button init method
        super().__init__(**kwargs)

    def on_press(self):
        """called when the event box is pressed
        - sets this event to be current
        - enables layouts
        - updates visuals
        - scrolls textboxes back to the start"""
        # This is now the current event
        self.app.select_event(self.event)

    def on_open_btn(self):
        """Called by button on event box
        Opens the file/folder associated with the event"""
        # Open that folder in the explorer
        p_open('explorer "' + str(self.experiment.directory) + '"')
        

class EventList(ScrollView):
    """scrolling widget which holds events"""

    def __init__(self, **kwargs):
        """init method for the scrolling widget"""
        # Save app as an attribute
        self.app = App.get_running_app()
        # Call ScrollView init method
        super(EventList, self).__init__(**kwargs)

    def clear_list(self, boxes_only=False):
        # While there are still boxs
        while len(self.grid_layout.children) != 0:
            # Get the first box
            box = self.grid_layout.children[0]
            # Remove the first box
            self.grid_layout.remove_widget(box)
        # If not only clearing boxes
        if not boxes_only:
            # clear experiment objects
            self.app.events.clear()
        # Update visual stuff
        self.window.update_fields()

    def on_current_event(self, instance, current_event):
        self.update_is_selected()

    def update_is_selected(self):
        # For every box
        for evt_box in self.grid_layout.children:
            # If not selected
            if evt_box.event != self.app.current_event:
                evt_box.is_selected = False
            # If selected
            else:
                evt_box.is_selected = True

    def on_x_btn(self, box, screen_id):
        """called when an x button on a box is pressed
        - disables the layouts because there is nothing selected now
        - removes the events
        - updates visuals"""
        # Remove that event
        self.grid_layout.remove_widget(box)
        # If on first screen after main
        if screen_id in ["TD1"]:
            # Remove the event
            self.app.remove_event(box.event)
        else:
            # Just deselect the event
            self.app.deselect_all_events()
        # Update visual stuff
        self.window.update_fields()
