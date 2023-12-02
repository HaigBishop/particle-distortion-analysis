"""
Module:  All classes related to Import Experiments Screen 3
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty
from kivy.uix.image import Image

# Import modules for dealing with files
from cv2 import flip
import cv2
import numpy as np

# Import local modules
from popup_elements import BackPopup
from jobs import ExperimentBox
from file_management import kivify_image

class IE3Window(Screen):
    """position -> force screen"""
    # True when using ion current data
    use_ion = BooleanProperty(False)
    # True when the slider is positioned on an event
    slider_on_event = BooleanProperty(False) 
    # True when ready for start - False when ready for stop
    ready_for_start = BooleanProperty(True) 


    def __init__(self, **kwargs):
        """init method for IE3 screen"""
        # Call ScrollView init method
        super(IE3Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def on_proceed(self):
        """called by pressing the 'Proceed' button."""
        pass

    def load_experiments(self):
        """Called by previous screen when migrating experiments over.
            Initialises exp boxes. Updates selection and visuals."""
        for experiment in self.app.experiments:
            # Create the accompanying list box
            new_exp_box = ExperimentBox(experiment, self)
            self.exp_scroll.grid_layout.add_widget(new_exp_box)
        # Set the last experiment added as the current job
        self.app.deselect_all_experiments()
        self.app.select_experiment(experiment)
        # Update everything visually
        self.update_fields()

    def update_fields(self):
        """Updates visuals. Depends on current experiment, etc."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Update with current experiment's values
            self.location_label.text = str(current.vid_loc)
            self.update_video()
            # Update frame label
            self.frame_label.text = 'Frame: ' + str(current.current_frame) + '/' + str(current.num_frames)
            # Update ion current file select section
            if self.use_ion and current.ion_loc != '':
                self.ion_location_label.text = str(current.ion_loc)
                self.ion_view.update_view()
            else:
                self.ion_location_label.text = 'No file selected'
                self.ion_view.update_view()
        else:
            # Update slider
            self.video_slider.value = 0
            # Reset with defaults
            self.location_label.text = "No experiment selected"
            self.video_widget.texture = None
            self.ion_location_label.text = 'No file selected'
            # Update frame label
            self.frame_label.text = ''
            self.ion_view.texture = None

    def update_video(self):
        """Update the video view by displaying the current frame."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get the first frame and flip for Kivy
            image = flip(current.get_frame(self.video_slider.value_normalized), 0)
            # Convert the image to a format useable for Kivy
            self.video_widget.texture = kivify_image(image)

    def on_back_btn(self):
        """called by back btn
        - makes a BackPopup object
        - if there are no experiments, it immediately closes it"""
        # If there are any experiments
        if len(self.app.experiments) > 0:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup("IE1")
            # Open it
            popup.open()
        # If there are not experiments
        else:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup("IE1")
            # THEN IMMEDIATELY CLOSE IT
            popup.on_answer("yes")
    
    def add_start_here(self):
        """Called by 'Enter Start' button - Adds an event start if valid"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            new_start = int(current.current_frame)
            ranges = current.event_ranges
            # Find if start is valid
            start_is_valid = True
            for start, end in ranges:
                # If new start overlaps with old ranges
                if start <= new_start <= end:
                    start_is_valid = False
                    break
            # If start is valid
            if start_is_valid:
                # Success! Add start.
                current.event_start_frame = new_start
                self.ready_for_start = False
        # update slider_on_event
        self.update_slider_on_event()
        # Update everything visually
        self.update_fields()
    
    def add_stop_here(self):
        """Called by 'Enter Stop' button - Adds an event stop if valid"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            ranges = current.event_ranges
            new_range = (current.event_start_frame, int(current.current_frame))
            # Find if range is valid
            range_is_valid = True
            # If stop smaller than start
            if new_range[0] >= new_range[1]:
                range_is_valid = False
            else:
                # Check for overlaps
                for old_range in ranges:
                    overlap_1 = (new_range[0] <= old_range[1] and new_range[1] >= old_range[0])
                    overlap_2 = (old_range[0] <= new_range[1] and old_range[1] >= new_range[0])
                    # If new range overlaps with old ranges
                    if overlap_1 or overlap_2:
                        range_is_valid = False
                        break
            # If range is valid
            if range_is_valid:
                # Success! Add range.
                current.event_start_frame = None
                current.event_ranges.append(new_range)
                self.ready_for_start = True
        # update slider_on_event
        self.update_slider_on_event()
        # Update everything visually
        self.update_fields()
    
    def remove_here(self):
        """Called by 'Remove' button - Removes a start or an event if slider is on one."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            current_frame = int(current.current_frame)
            event_start_frame = current.event_start_frame
            event_ranges = current.event_ranges
            # If slider is on start
            if event_start_frame is not None and event_start_frame == current_frame:
                # Remove start
                current.event_start_frame = None
                self.ready_for_start = True
            else:
                # Find if on event range
                for start, end in event_ranges:
                    if start <= current_frame <= end:
                        # Remove range
                        current.event_ranges.remove((start, end))
                        break
        # update slider_on_event
        self.update_slider_on_event()
        # Update everything visually
        self.update_fields()

    def update_slider_on_event(self):
        """Updates the self.slider_on_event boolean."""
        on_event = False
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            current_frame = current.current_frame
            event_start_frame = current.event_start_frame
            event_ranges = current.event_ranges
            # If slider is on start
            if event_start_frame is not None and event_start_frame == current_frame:
                on_event = True
            # If still false
            else:
                # Find if frame is in ranges
                for start, end in event_ranges:
                    if start <= current_frame <= end:
                        on_event = True
                        break
        # Update with final value
        self.slider_on_event = on_event
            

    def on_current_experiment(self, instance, current_experiment):
        """Called when current experiment changes. Updates slider"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Update slider
            self.video_slider.value = (current.current_frame - 1) / (current.num_frames - 1)
        else:
            # Update slider
            self.video_slider.value = 0
        # Update bools
        self.ready_for_start = False if current is None else current.event_start_frame is None
        self.update_slider_on_event()

    def on_slider(self):
        """Called when slider value changes. Updates things."""
        # update slider_on_event
        self.update_slider_on_event()
        # Update everything visually
        self.update_fields()


class IonCurrentView(Image):
    """The widget which holds the image"""

    def __init__(self, **kwargs):
        """init method for the image widget in PS2"""
        # Call Image init method
        super(IonCurrentView, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def set_frame(self, pos):
        """Changes slider position based on click position on window."""
        # If user clicked on the ion current view
        if self.collide_point(*pos):
            # Take position as proportion of widget width
            self.video_slider.value = (pos[0] - self.x) / self.width
        # update slider_on_event
        self.ie3_window.update_slider_on_event()

    def on_size(self, instance, current_size):
        """Called when size of widget changes."""
        # Update the widget's texture
        self.update_view()
    
    def update_view(self):
        """Updates the widget's texture."""
        # Get widget dimensions
        width, height = int(self.width), int(self.height)
        # Make white image
        white_image = 255 * np.ones((height, width, 3), dtype=np.uint8)
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            ranges = current.event_ranges
            num_frames = current.num_frames
            current_frame = current.current_frame
            event_start_frame = current.event_start_frame
            # Draw grey rectangle at x position of slider (for frame)
            x1 = int((width - 1) * (current_frame - 1) / (num_frames))
            x2 = int((width - 1) * (current_frame) / (num_frames))
            # Draw vertical blue box at frame of start of event
            cv2.rectangle(white_image, (x1, 0), (x2, height), (212, 212, 212), -1)
            # Draw start line
            if event_start_frame is not None:
                x1 = int((width - 1) * (event_start_frame - 1) / (num_frames))
                x2 = int((width - 1) * (event_start_frame) / (num_frames))
                # Draw vertical blue box at frame of start of event
                cv2.rectangle(white_image, (x1, 0), (x2, height), (255, 172, 89), -1)
            # Draw event ranges
            for start_frame, stop_frame in ranges:
                start_x1 = int((width - 1) * (start_frame - 1) / (num_frames))
                stop_x2 = int((width - 1) * (stop_frame) / (num_frames))
                # Draw range
                cv2.rectangle(white_image, (start_x1, 0), (stop_x2 - 1, height), (202, 202, 202), -1)
                # Draw edges
                cv2.line(white_image, (start_x1, 0), (start_x1, height), (42, 42, 42), 1)
                cv2.line(white_image, (stop_x2, 0), (stop_x2, height), (42, 42, 42), 1)
        # Draw vertical red line at x position of slider
        x = int((width - 1) * self.video_slider.value_normalized)
        cv2.line(white_image, (x, 0), (x, height), (0, 0, 255), 1)
        # Set as texture
        self.texture = kivify_image(white_image)
