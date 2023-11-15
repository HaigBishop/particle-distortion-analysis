"""
Module:  All classes related to Tracking Deformation Screen 1
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

# Import modules for dealing with files
from os.path import getctime
from datetime import datetime
import os
import re
from subprocess import Popen as p_open
from plyer import filechooser


# Import local modules
from popup_elements import BackPopup
from jobs import Experiment

class IE1Window(Screen):
    """position -> force screen"""

    def __init__(self, **kwargs):
        """init method for IE1 screen"""
        # Call ScrollView init method
        super(IE1Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def detect(self):
        """called by pressing the Detect button
        starts the detection process"""
        pass

    def select_files(self):
        """called when [select file(s)] button is pressed
        - opens the file select window
        - selection is sent to self.selected()"""
        # Only allow selection of TDMS
        filters = [("TDMS files", "*.tdms")]
        # Open folder selector window - send selection to self.selected
        filechooser.open_file(
            on_selection=self.selected, 
            title="Select file(s)", 
            filters=filters,
            multiple=True
        )

    def selected(self, selection):
        """receives selection from selector window
        - checks if the selections are valid
        - if they are it adds them as experiments
        - if any are not valid it will display an error string"""
        for file_loc in selection:
            # Create a experiment object
            new_experiment = Experiment(file_loc)

    def update_fields(self):
        """updates the text inputs and the 'location label'
        - new values are determined by the current experiment"""
        # If there is a current experiment
        current = self.app.current_experiment()
        if current is not None:
            # Update with current experiment's values
            self.location_label.text = str(current.vid_loc)
            self.name_input.text = str(current.name)
        else:
            # Reset with defaults
            self.location_label.text = "No file(s) selected"
            self.name_input.text = ""

    def on_name_text(self, text):
        """called when name text input is changed
        - takes the new text
        - updates the current experiment if there is one"""
        # If there is a current experiment
        current = self.app.current_experiment()
        if current is not None:
            # Update the experiment's name
            current.name = text

    def on_back_btn(self):
        """called by back btn
        - makes a BackPopup object
        - if there are no experiments, it immediately closes it"""
        # If there are any experiments
        if len(self.app.experiments) > 0:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup("main")
            # Open it
            popup.open()
        # If there are not experiments
        else:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup("main")
            # THEN IMMEDIATELY CLOSE IT
            popup.on_answer("yes")

    def _on_file_drop(self, file_path, x, y):
        """called when a file is dropped on this screen
        - sends the file path to the selected method"""
        self.selected([file_path])


class ExperimentList(ScrollView):
    """scrolling widget in IE1"""

    def __init__(self, **kwargs):
        """init method for the scrolling widget in IE1"""
        # Call ScrollView init method
        super(ExperimentList, self).__init__(**kwargs)

    def on_x_btn(self, box):
        """called when an x button on a box is pressed or using clear_experiments
        - disables the layouts because there is nothing selected now
        - removes the experiments
        - updates visuals"""
        # Disabled layouts
        self.ie1_window.param_grid_layout.disabled = True
        self.ie1_window.name_grid_layout.disabled = True
        # Remove that experiment
        self.grid_layout.remove_widget(box)
        # Update current experiment to none
        self.app.deselect_all_experiments()
        # Update visual stuff
        self.ie1_window.update_fields()
        self.ie1_window.update_experiment_selected()


class ExperimentBox(Button):
    """experiment widget on the IE1ScrollView widget"""

    def __init__(self, experiment, **kwargs):
        """init method for experiment boxes on a experiment list scrollview"""
        self.experiment = experiment
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
        self.experiment.is_current = True
        # Enable layouts
        self.ie1_window.param_grid_layout.disabled = False
        self.ie1_window.name_grid_layout.disabled = False
        # Update the visuals
        self.ie1_window.update_fields()
        self.ie1_window.update_experiment_selected()

    def on_open_btn(self):
        """Called by button on experiment box
        Opens the file/folder associated with the experiment"""
        # Find last slash
        s = str(self.experiment.vid_loc).rfind("\\") + 1
        # E.g. 'C:\Desktop\folder\'
        path = str(self.experiment.vid_loc)[:s]
        # Open that folder in the explorer
        p_open('explorer "' + str(path) + '"')
