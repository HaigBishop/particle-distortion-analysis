"""
Module:  All classes related to Import Experiments Screen 1
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty
from kivy.clock import Clock

# Import modules for dealing with files
from plyer import filechooser
import cv2
import os

# Import local modules
from popup_elements import BackPopup, ErrorPopup
from jobs import Experiment, ExperimentBox
from file_management import is_ion_file, is_video_file, kivify_image, get_frame

class IE1Window(Screen):
    """position -> force screen"""
    ion_files_attached = BooleanProperty(False)
    is_loading = BooleanProperty(False)

    def __init__(self, **kwargs):
        """init method for IE1 screen"""
        # Call ScrollView init method
        super(IE1Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def schedule_with_load(self, function):
        """Schedules a function call and sets loading to True."""
        # Start loading
        self.is_loading = True
        # Schedule function
        Clock.schedule_once(function)

    def on_proceed(self, with_ion=False):
        """called by pressing one of the Proceed buttons.
        - if it was the 'Proceed Without Current Data' button:
            with_ion is False 
        - if it was the 'Proceed With Current Data' button:
            with_ion is True """
        # Check if the selected video data is valid
        vid_errors = self.check_vids()
        # Check if the selected ion data is valid (if using that data)
        if with_ion:
            ion_errors = self.check_ions()
        else:
            ion_errors = []
        # If there are issues with the data
        if vid_errors + ion_errors != []:
            # Make pop up - alerts of invalid data
            popup = ErrorPopup()
            # Adjust the text on the popup
            popup.error_label.text = "Invalid Data:\n" + "".join(vid_errors)
            popup.open()
        # If no issues with the data
        else:
            # Set use_ion
            ie3_window = self.app.root.get_screen("IE3")
            ie3_window.use_ion = with_ion
            # Change screen to IE3
            self.app.root.current = "IE3"
            self.app.root.transition.direction = "left"
            # Load experiments on new screen
            ie3_window.load_experiments()

    def check_vids(self):
        """Checks that the video is suitable.
        We know it is a video file and can be opened, but let's also check:
        - number of frames is 3 or more
        - resolution is more than 256x256
        - number of channels is 1 or 3
        - it is not a duplicate file"""
        errors = []
        name_list = []
        vid_loc_list = []
        # Loop all experiments
        for exp in self.app.experiments:
            cap = exp.cap
            print(cap)
            # Check number of frames
            num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if num_frames < 3:
                errors.append("invalid number of video frames (" + str(exp.name) + ")\n")
            # Check resolution
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if width < 128 or height < 128:
                errors.append("invalid video resolution (" + str(exp.name) + ")\n")
            # Check number of channels
            # (by getting the shape of the first frame)
            frame = get_frame(cap, 1)
            _, _, num_channels = frame.shape
            if int(num_channels) not in [1, 3]:
                errors.append("invalid number of video channels (" + str(exp.name) + ")\n")
            # Add this job's name and file loc to lists (to check for duplicates)
            name_list.append(exp.name)
            vid_loc_list.append(exp.vid_loc)
        # Check for duplicate files
        if len(vid_loc_list) != len(set(vid_loc_list)):
            # Duplicate files
            errors.append(" • duplicate files\n")
        # Check for duplicate names
        elif len(name_list) != len(set(name_list)):
            # Duplicate names
            errors.append(" • duplicate names\n")
        # Return the errors which have been found
        return list(set(errors))

    def check_ions(self):
        """Checks that the ion current data is suitable.
        We know it is a TDMS file and can be opened, but let's also check:
        - has 3 or more samples
        - it is not a duplicate file"""
        errors = []
        ion_loc_list = []
        # Loop all experiments
        for exp in self.app.experiments:
            # Check number of samples
            if exp.ioncurr_len < 3 or exp.strobe_len < 3:
                errors.append("invalid number of ion current samples (" + str(exp.name) + ")\n")
            # Add this job's ion file loc to list (to check for duplicates)
            ion_loc_list.append(exp.ion_loc)
        # Check for duplicate files
        if len(ion_loc_list) != len(set(ion_loc_list)):
            # Duplicate files
            errors.append(" • duplicate files\n")
        # Return the errors which have been found
        return list(set(errors))
    
    def try_select_ions(self, *args):
        """For every experiment, if it doesn't already have an ion current file...
        Look for a tdms file of the same name and try use that."""
        # For all experiments
        for exp in self.app.experiments:
            # If it has no ion current file
            if exp.ion_loc == '' and  exp.vid_loc != '':
                # Swap the file extension to tdms
                i = str(exp.vid_loc).rfind(".") + 1
                ion_loc = str(exp.vid_loc)[:i] + 'tdms'
                if os.path.isfile(ion_loc):
                    # Load that shit!
                    self.ion_selected([ion_loc], experiment=exp)
        # Done loading
        self.is_loading = False

    def select_vid_files(self, *args):
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

    def select_ion_file(self, *args):
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
            # Done loading
            self.is_loading = False
        else:
            # Set the last experiment added as the current job
            self.app.select_experiment(new_experiment)
            # Enable layouts
            self.param_grid_layout.disabled = False
            self.name_grid_layout.disabled = False
            # Schedule to try to select an ion file for these new experiments
            Clock.schedule_once(self.try_select_ions)
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

    def ion_selected(self, selection, experiment=None, *args):
        if experiment is None:
            experiment = self.app.current_experiment
        # Set booleans to test if selection is valid
        there_is_current, invalid_type = True, False
        for file_loc in selection:
            if is_ion_file(file_loc):
                # If there is a current experiment
                if experiment is not None:
                    # Add it to the current experiment
                    experiment.add_ion_file(file_loc)
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
        # Done loading
        self.is_loading = False

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
            # Convert the image to a format useable for Kivy
            self.image_widget.texture = kivify_image(current.first_frame)

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
            