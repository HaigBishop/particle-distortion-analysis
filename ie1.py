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
from kivy.properties import BooleanProperty

# Import modules for dealing with files
from subprocess import Popen as p_open
from plyer import filechooser
from cv2 import flip

# Import local modules
from popup_elements import BackPopup
from jobs import Experiment
from file_management import is_ion_file, is_video_file, kivify_image

class IE1Window(Screen):
    """position -> force screen"""
    ion_files_attached = BooleanProperty(False)

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

    def select_vid_files(self):
        """called when [select video file(s)] button is pressed
        - opens the file select window
        - selection is sent to self.selected()"""
        # Only allow selection of TDMS
        filters = [("AVI files", "*.avi")]
        # Open folder selector window - send selection to self.selected
        filechooser.open_file(
            on_selection=self.vid_selected, 
            title="Select file(s)", 
            filters=filters,
            multiple=True
        )

    def select_ion_file(self):
        """called when [select ion current file] button is pressed
        - opens the file select window
        - selection is sent to self.selected()"""
        # Only allow selection of TDMS
        filters = [("TDMS files", "*.tdms")]
        # Open folder selector window - send selection to self.selected
        filechooser.open_file(
            on_selection=self.ion_selected, 
            title="Select file(s)", 
            filters=filters,
            multiple=False
        )

    def vid_selected(self, selection):
        """receives selection from selector window
        - checks if the selections are valid
        - if they are it adds them as experiments
        - if any are not valid it will display an error string"""
        # Set booleans to test if selection is valid
        no_valid, duplicate, invalid_type = True, False, False
        for file_loc in selection:
            # If is is a genuine selection of valid type
            if is_video_file(file_loc):
                # If it doesn't already exist
                if not self.app.duplicate_experiment(file_loc):
                    # Create a experiment object
                    new_experiment = Experiment(file_loc)
                    # Add to the list
                    self.app.add_experiment(new_experiment)
                    # Create the accompanying list box
                    new_exp_box = ExperimentBox(new_experiment, self)
                    self.exp_scroll.grid_layout.add_widget(new_exp_box)
                    no_valid = False
                # It is a duplicate!
                else:
                    duplicate = True
            # It is invalid type!
            else:
                invalid_type = True
        # If none are valid
        if no_valid:
            # Deselect any jobs, update location label
            self.app.deselect_all_experiments()
            # Disable layouts
            self.param_grid_layout.disabled = True
            self.name_grid_layout.disabled = True
        else:
            # Set the last experiment added as the current job
            self.app.select_experiment(new_experiment)
            # Enable layouts
            self.param_grid_layout.disabled = False
            self.name_grid_layout.disabled = False
        # Update everything visually
        self.update_fields()
        # If there was a failed selection
        if duplicate or invalid_type:
            # Make an error string describing the issue
            error_string = ""
            if duplicate == True:
                # Update error string
                error_string += "File duplicate(s)  "
            if invalid_type == True:
                # Update error string
                error_string += "Incorrect file type(s)"
            # Update location label
            self.location_label.text = error_string

    def ion_selected(self, selection):
        # Set booleans to test if selection is valid
        there_is_current, invalid_type = True, False
        for file_loc in selection:
            if is_ion_file(file_loc):
                # If there is a current experiment
                if self.app.current_experiment is not None:
                    # Add it to the current experiment
                    self.app.current_experiment.add_ion_file(file_loc)
                else:
                    there_is_current = False
            # It is invalid type!
            else:
                invalid_type = True
        # Update ion attached boolean
        self.update_ion_files_attached()
        # Update everything visually
        self.update_fields()
        # If there was a failed selection
        if not there_is_current or invalid_type:
            # Make an error string describing the issue
            error_string = ""
            if there_is_current == False:
                # Update error string
                error_string += "No current experiment  "
            if invalid_type == True:
                # Update error string
                error_string += "Incorrect file type(s)"
            # Update location label
            self.ion_location_label.text = error_string

    def on_ion_x_btn(self):
        """Called when the 'x' button next two the ion current file selection is pressed."""
        self.app.current_experiment.remove_ion_file()
        # Update ion attached boolean
        self.update_ion_files_attached()
        # Update everything visually
        self.update_fields()
    
    def update_ion_files_attached(self):
        any_exps = len(self.app.experiments) != 0
        self.ion_files_attached = any_exps and all([exp.ion_loc != '' for exp in self.app.experiments])


    def update_fields(self):
        """updates the text inputs and the 'location label'
        - new values are determined by the current experiment"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Update with current experiment's values
            self.location_label.text = str(current.vid_loc)
            self.name_input.text = str(current.name)
            self.update_image_preview()
            # Update ion current file select section
            if current.ion_loc != '':
                self.ion_location_label.text = str(current.ion_loc)
            else:
                self.ion_location_label.text = 'No file selected'
        else:
            # Reset with defaults
            self.location_label.text = "No experiment selected"
            self.name_input.text = ""
            self.image_widget.texture = None
            self.ion_location_label.text = 'No file selected'

    def on_name_text(self, text):
        """called when name text input is changed
        - takes the new text
        - updates the current experiment if there is one"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Update the experiment's name
            current.name = text

    def update_image_preview(self):
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get the first frame and flip for Kivy
            image = flip(current.first_frame, 0)
            # Convert the image to a format useable for Kivy
            self.image_widget.texture = kivify_image(image)

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

    def on_experiments(self, instance, experiments):
        # Update ion attached boolean
        self.update_ion_files_attached()

    def _on_file_drop(self, file_path):
        """called when a file is dropped on this screen
        - sends the file path to the selected method"""
        # If it is a TDMS file send it to the ion selection method
        if file_path[-5:].lower() == '.tdms':
            self.ion_selected([file_path])
        else:
            self.vid_selected([file_path])


class ExperimentList(ScrollView):
    """scrolling widget in IE1"""

    def __init__(self, **kwargs):
        """init method for the scrolling widget in IE1"""
        # Save app as an attribute
        self.app = App.get_running_app()
        # Call ScrollView init method
        super(ExperimentList, self).__init__(**kwargs)

    def clear_list(self):
        # Disabled layouts
        self.window.param_grid_layout.disabled = True
        self.window.name_grid_layout.disabled = True
        # While there are still jobs
        while len(self.grid_layout.children) != 0:
            # Remove the first job
            self.grid_layout.remove_widget(self.grid_layout.children[0])
        # clear experiment objects
        self.app.experiments.clear()
        # Update visual stuff
        self.window.update_fields()

    def on_x_btn(self, box):
        """called when an x button on a box is pressed
        - disables the layouts because there is nothing selected now
        - removes the experiments
        - updates visuals"""
        # Disabled layouts
        self.window.param_grid_layout.disabled = True
        self.window.name_grid_layout.disabled = True
        # Remove that experiment
        self.grid_layout.remove_widget(box)
        # Update current experiment to none
        self.app.remove_experiment(box.experiment)
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



class ExperimentBox(Button):
    """experiment widget on the IE1ScrollView widget"""
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
        # Enable layouts
        self.window.param_grid_layout.disabled = False
        self.window.name_grid_layout.disabled = False
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
