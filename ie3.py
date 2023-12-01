"""
Module:  All classes related to Import Experiments Screen 3
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty
from kivy.uix.image import Image
from kivy.graphics.texture import Texture

# Import modules for dealing with files
from subprocess import Popen as p_open
from plyer import filechooser
from cv2 import flip
import cv2
import numpy as np

# Import local modules
from popup_elements import BackPopup, ErrorPopup
from jobs import ExperimentBox, ExperimentList
from file_management import is_ion_file, is_video_file, kivify_image

class IE3Window(Screen):
    """position -> force screen"""
    use_ion = BooleanProperty(False)

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
        """updates the text inputs and the 'location label'
        - new values are determined by the current experiment"""
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
                self.ion_view.texture = None
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

    def on_current_experiment(self, instance, current_experiment):
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Update slider
            self.video_slider.value = current.current_frame / current.num_frames
        else:
            # Update slider
            self.video_slider.value = 0


class IonCurrentView(Image):
    """The widget which holds the image"""

    def __init__(self, **kwargs):
        """init method for the image widget in PS2"""
        # Call Image init method
        super(IonCurrentView, self).__init__(**kwargs)

    def on_size(self, instance, current_size):
        self.update_view()
    
    def update_view(self):
        # Get widget dimensions
        width, height = int(self.width), int(self.height)
        # Make white image
        white_image = 255 * np.ones((height, width, 3), dtype=np.uint8)
        # Draw vertical red line at x position of slider
        x = int((width - 1) * self.video_slider.value_normalized)
        cv2.line(white_image, (x, 0), (x, height), (0, 0, 255), 1)
        # Set as texture
        self.texture = kivify_image(white_image)