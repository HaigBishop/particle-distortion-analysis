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
import pandas as pd

# Import local modules
from file_management import read_vid, get_frame, count_frames, file_date, fft_and_filter, normalise_and_smooth_sig, align_sig_to_frames, read_tdms
from tracking import detect_start, get_y_maximums_multiple_frame_crops

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
        self.current_frame_num = first_frame_num
        self.first_frame_num = first_frame_num
        self.last_frame_num = last_frame_num
        self.num_frames = last_frame_num - first_frame_num + 1
        self.first_frame = get_frame(self.experiment.cap, first_frame_num)
        # Avoid accessing this list directly, use the get_frame method instead, which uses frame numbering
        self.all_frames = [get_frame(self.experiment.cap, i) for i in range(first_frame_num, last_frame_num + 1)]
       
        # Ion current file
        self.ion_data = ion_data

        # Start point features (from prediction/user input)
        self.particle_pos = None
        self.particle_radius = None
        self.pipette_angle = None
        self.left_bottom_x = None
        self.right_bottom_x = None
        self.distortion_y_positions = None
        self.crop_region = None

        # A CSV file attached to this event which describes it and its event
        self.csv_file_loc = None


    def get_frame(self, frame_num, direct_indexing=False):
        """Returns the frame at the given frame number"""
        # If frame_num is 'current', use the current frame number
        if frame_num == 'current':
            frame_num = self.current_frame_num
        # If direct indexing is True, use the index directly
        if direct_indexing:
            idx = frame_num
        # Otherwise, use the frame number
        else:
            idx = frame_num - self.first_frame_num
        # If the index is out of bounds
        if idx < 0 or idx >= len(self.all_frames):
            # Throw an error
            raise ValueError(f"Frame number is out of range for this event. Frame number: {frame_num}, Event range: {self.first_frame_num} to {self.last_frame_num}")
        # Return the frame
        return self.all_frames[idx]

    def predict_start(self):
        """Predict the position, angle, etc of the start point.
        Then, update those values so they can be displayed... or exported etc."""
        # Run the first frame through the algorithm
        particle_pos, particle_radius, pipette_angle, left_bottom_x, right_bottom_x = detect_start(self.first_frame, display=False)
        # Update the values 
        # These values were made for a different purpose unfortunately, but we are repurposing them :)
        self.particle_pos = (int(particle_pos[0]), int(particle_pos[1]))
        self.particle_radius = particle_radius
        self.pipette_angle = pipette_angle
        self.left_bottom_x = left_bottom_x
        self.right_bottom_x = right_bottom_x
        # Calculate the slope of the pipette
        # y is negative because the image is flipped
        height = self.first_frame.shape[0]
        line_start = (int(self.left_bottom_x), int(-0)) # Top of line
        line_end = (int(self.left_bottom_x + self.pipette_angle * height), int(-height)) # Bottom of line
        # This slop is the slope of the lines running along the length of the pipette
        slope = (line_start[1] - line_end[1]) / (line_start[0] - line_end[0])
        # This slope is the slope of the line running along the bottom of the pipette at the tip (the width of the pipette)
        pipette_tip_slope = -1/slope
        # This point is the point of the particle furthest into the pipette but still on the edge of the perfect circle
        # Calculate angle from slope (arctan gives angle in radians)
        angle = np.arctan(slope)
        # Calculate the offset from particle_pos using trigonometry
        x_offset = self.particle_radius * np.cos(angle)
        y_offset = self.particle_radius * np.sin(angle)
        # Calculate the tip coordinates
        particle_tip_x = self.particle_pos[0] + x_offset
        particle_tip_y = self.particle_pos[1] - y_offset # Negative because the image is flipped
        # Given the line made by the particle tip and the pipette_tip_slope, calculate y value on this line at x_centre
        x_centre = self.first_frame.shape[1] / 2
        whyy = pipette_tip_slope * (x_centre - particle_tip_x)
        pipette_tip_centre_y = particle_tip_y - whyy # Negative because the image is flipped
        pipette_tip_centre_y += 10 # We move down by 10 because it is always an overshoot (due to repurposing)
        self.particle_tip_x = particle_tip_x
        self.particle_tip_y = particle_tip_y
        self.pipette_tip_centre_y = pipette_tip_centre_y
        self.pipette_tip_centre_x = x_centre
        self.pipette_tip_slope = pipette_tip_slope

    def track_distortion(self):
        """Tracks the distortion of the particle"""
        # Determine where to crop the images
        num_radii_below_top_of_particle = 0.35
        num_pixels_below_top_of_particle = int(num_radii_below_top_of_particle * self.particle_radius)
        num_radii_above_particle = 0.55
        num_pixels_above_centre_of_particle = int(self.particle_radius * (1 + num_radii_above_particle))
        minimum_width_of_crop = 2
        num_radii_for_width_of_crop = 0.15

        # Calculate crop dimensions based on particle position and radius
        top_y = max(0, int(self.particle_pos[1] - num_pixels_above_centre_of_particle))
        bottom_y = min(self.first_frame.shape[0], int(self.particle_pos[1] - self.particle_radius + num_pixels_below_top_of_particle))
        crop_width = max(minimum_width_of_crop, 
                        int(self.particle_radius * num_radii_for_width_of_crop * 2))
        left_x = max(0, int(self.particle_pos[0] - crop_width // 2))
        right_x = min(self.first_frame.shape[1], int(self.particle_pos[0] + crop_width // 2))

        # Get all cropped frames
        cropped_frames = []
        for frame in self.all_frames:
            cropped = frame[top_y:bottom_y, left_x:right_x]
            cropped_frames.append(cropped)

        # Smoothing starts at the top of the particle (but in terms of the cropped image)
        starting_smooth_position = int(num_radii_above_particle * self.particle_radius) + 1
        # Use get_y_maximums_multiple_frame_crops to predict the distortion
        # (y_maximums is a list of y positions, starting at 1 (top of cropped image) and goes to the bottom of the cropped image)
        y_maximums = get_y_maximums_multiple_frame_crops(cropped_frames, smooth=True, non_decreasing=True, 
                                                         starting_smooth_position=starting_smooth_position, 
                                                         display=False)

        # Convert these positions to be relative to the uncropped frames and save as attributes
        self.distortion_y_positions = [y + top_y - 1 for y in y_maximums]
        self.crop_region = (top_y, bottom_y, left_x, right_x)

    def get_distortion_data_for_export(self):
        """Returns a pandas dataframe of the distortion data for export.
        Columns are: 
            experiment_frame, event_frame, dL_pixels, 
            particle_tip_x, particle_tip_y, 
            particle_centre_x, particle_centre_y, particle_radius
        """
        # Create lists to hold the data
        data = {
            'experiment_frame': [],
            'event_frame': [],
            'dL_pixels': [],
            'particle_tip_x': [],
            'particle_tip_y': [],
            'particle_centre_x': [],
            'particle_centre_y': [],
            'particle_radius': []
        }
        
        # For each frame in the event
        for frame_idx in range(len(self.distortion_y_positions)):
            # Calculate the experiment frame number
            exp_frame = frame_idx + self.first_frame_num
            # Calculate event frame number (1-based)
            evt_frame = frame_idx + 1
            
            # Get y position for this frame
            y_pos = self.distortion_y_positions[frame_idx]
            
            # Calculate dL (distance from initial position)
            initial_y = self.distortion_y_positions[0]
            dL = int(abs(y_pos - initial_y))
            
            # Add the data for this frame
            data['experiment_frame'].append(exp_frame)
            data['event_frame'].append(evt_frame)
            data['dL_pixels'].append(dL)
            data['particle_tip_x'].append(round(self.particle_tip_x))
            data['particle_tip_y'].append(round(self.distortion_y_positions[frame_idx]))
            data['particle_centre_x'].append(round(self.particle_pos[0]))
            data['particle_centre_y'].append(round(self.particle_pos[1]))
            data['particle_radius'].append(round(self.particle_radius))
        
        # Create and return the DataFrame
        return pd.DataFrame(data)

    def drawn_first_frame(self, zoomed, hidden=False):
        """Take the first frame, draw the position, angle, etc. Return it.
        - made for TD2"""
        # Grab a copy of the first frame
        frame = self.first_frame.copy()
        # If not hidden
        if not hidden:
            # Draw the particle
            if self.particle_pos is not None and self.particle_radius is not None:
                cv2.circle(frame, (int(self.particle_pos[0]), int(self.particle_pos[1])), int(self.particle_radius), (0, 0, 255), 1)
                # Draw the centre point of the particle
                cv2.circle(frame, (int(self.particle_pos[0]), int(self.particle_pos[1])), 1, (0, 0, 255), 1)
            # Draw the pipette tip
            if self.pipette_angle is not None and self.left_bottom_x is not None and self.right_bottom_x is not None:
                # Draw the pipette tip line across the whole width using pipette_tip_centre_y and pipette_tip_slope
                y_rise_half_width = (self.pipette_tip_slope * self.first_frame.shape[1])/2
                left_xy = (int(0), int(self.pipette_tip_centre_y + y_rise_half_width))
                right_xy = (int(self.first_frame.shape[1]), int(self.pipette_tip_centre_y - y_rise_half_width))
                cv2.line(frame, left_xy, right_xy, (0, 0, 255), 1)
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

    def drawn_specific_frame(self, frame_num, zoomed, hidden=False):
        """Draws a specific frame. 
        Main difference to drawn_first_frame is that this is made for TD3, where the top line is also shown. """
        if frame_num == 'current':
            frame_num = self.current_frame_num
        # Check frame_num is within the range of the event
        if frame_num < self.first_frame_num or frame_num > self.last_frame_num:
            # Raise an informative error
            raise ValueError(f"Frame number is out of range for this event. Frame number: {frame_num}, Event range: {self.first_frame_num} to {self.last_frame_num}")
        # Grab the frame (a copy)
        frame = get_frame(self.experiment.cap, frame_num - 1).copy()
        # If not hidden
        if not hidden:
            # Draw the particle
            if self.particle_pos is not None and self.particle_radius is not None:
                cv2.circle(frame, (int(self.particle_pos[0]), int(self.particle_pos[1])), int(self.particle_radius), (0, 0, 255), 1)
                # Draw the centre point of the particle
                cv2.circle(frame, (int(self.particle_pos[0]), int(self.particle_pos[1])), 1, (0, 0, 255), 1)
            # # Draw the pipette tip
            # if self.pipette_angle is not None and self.left_bottom_x is not None and self.right_bottom_x is not None:
            #     # Draw the pipette tip line across the whole width using pipette_tip_centre_y and pipette_tip_slope
            #     y_rise_half_width = (self.pipette_tip_slope * self.first_frame.shape[1])/2
            #     left_xy = (int(0), int(self.pipette_tip_centre_y + y_rise_half_width))
            #     right_xy = (int(self.first_frame.shape[1]), int(self.pipette_tip_centre_y - y_rise_half_width))
            #     cv2.line(frame, left_xy, right_xy, (0, 0, 255), 1)
            if self.distortion_y_positions is not None:
                frame_index = frame_num - self.first_frame_num
                if frame_index < len(self.distortion_y_positions):
                    y_intercept = self.distortion_y_positions[frame_index]
                    x_intercept = self.particle_tip_x
                    slope = self.pipette_tip_slope
                    # Make a line using this slope and this point that the line should pass through
                    # Calculate points for line across whole frame width
                    x1 = 0
                    y1 = int(y_intercept - slope * (x_intercept - x1))
                    x2 = frame.shape[1]
                    y2 = int(y_intercept - slope * (x_intercept - x2))
                    start_point = (x1, y1)
                    end_point = (x2, y2)
                    cv2.line(frame, start_point, end_point, (0, 0, 255), 1)
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

    def move_down_pipette_tip(self):
        """Moves the pipette tip down"""
        # If pipette_tip_centre_y is within 10 pixels of the edge to prevent going out of bounds
        if self.pipette_tip_centre_y < self.first_frame.shape[0] - 10:
            self.pipette_tip_centre_y = self.pipette_tip_centre_y + 1

    def move_up_pipette_tip(self):
        """Moves the pipette tip up"""
        # If pipette_tip_centre_y is within 10 pixels of the edge to prevent going out of bounds
        if self.pipette_tip_centre_y > 10:
            self.pipette_tip_centre_y = self.pipette_tip_centre_y - 1

    def tilt_left_pipette_tip(self):
        """Tilts the pipette tip left"""
        # If angle is below 0.2
        if self.pipette_tip_slope < 0.2:
            # Move the pipette left
            self.pipette_tip_slope = self.pipette_tip_slope + 0.005
    
    def tilt_right_pipette_tip(self):
        """Tilts the pipette tip right"""
        # If angle is above -0.2
        if self.pipette_tip_slope > -0.2:
            # Move the pipette right
            self.pipette_tip_slope = self.pipette_tip_slope - 0.005

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
         
    def move_distortion_up(self, frame_num='current', maintain_nondecreasing=False):
        """Moves the distortion up"""
        # If frame_num is 'current', use the current frame number
        if frame_num == 'current':
            frame_num = self.current_frame_num
        # get the frame index
        frame_index = frame_num - self.first_frame_num
        # get the current y position
        current_y = self.distortion_y_positions[frame_index]
        # If the distortion is not at the top of the image
        if current_y > 1:
            new_y = current_y - 1
            # Move the distortion up
            self.distortion_y_positions[frame_index] = new_y
            # If maintain_nondecreasing
            if maintain_nondecreasing:
                # Get the next frame index
                next_frame_index = frame_index + 1
                # While the new y position is less than the next frame y position
                while next_frame_index in range(len(self.distortion_y_positions)) and new_y < self.distortion_y_positions[next_frame_index]:
                    # Make the distortion match
                    self.distortion_y_positions[next_frame_index] = new_y
                    # Get the next frame index
                    next_frame_index += 1

    def move_distortion_down(self, frame_num='current', maintain_nondecreasing=False):
        """Moves the distortion down"""
        # If frame_num is 'current', use the current frame number
        if frame_num == 'current':
            frame_num = self.current_frame_num
        # get the frame index
        frame_index = frame_num - self.first_frame_num
        # get the current y position
        current_y = self.distortion_y_positions[frame_index]
        # If the distortion is not at the bottom of the image
        if current_y < self.first_frame.shape[0] - 1:
            new_y = current_y + 1
            # Move the distortion down
            self.distortion_y_positions[frame_index] = new_y
            # If maintain_nondecreasing
            if maintain_nondecreasing:
                # Get the prev frame index
                prev_frame_index = frame_index - 1
                # While the new y position is greater than the prev frame y position
                while prev_frame_index in range(len(self.distortion_y_positions)) and new_y > self.distortion_y_positions[prev_frame_index]:
                    # Make the distortion match
                    self.distortion_y_positions[prev_frame_index] = new_y
                    # Get the prev frame index
                    prev_frame_index -= 1


    def update_pos(self, pos):
        """Takes a position (in terms of the original image) and updates the particle_pos
        Assumes the position is valid"""
        self.particle_pos = pos

    def previous_frame(self):
        """Moves to the previous frame"""
        # If the current frame number is greater than the first frame number
        if self.current_frame_num > self.first_frame_num:
            # Move to the previous frame
            self.current_frame_num = self.current_frame_num - 1

    def next_frame(self):
        """Moves to the next frame"""
        # If the current frame number is less than the last frame number
        if self.current_frame_num < self.last_frame_num:
            # Move to the next frame
            self.current_frame_num = self.current_frame_num + 1


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
